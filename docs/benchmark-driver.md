# Benchmark Driver Concept

The EMIP benchmark driver replays source events, issues query workloads,
records standing-query result streams, and measures whether a system under
test can maintain fresh and correct analytical state under load.

The reference implementation uses DuckDB as the batch oracle. DuckDB defines
the exact results for all standing and ad hoc queries at deterministic
event-time snapshots. Systems under test may maintain these results
incrementally, but their outputs are validated against the DuckDB oracle.

## Timing Model

The driver replays data according to the original event timestamps. Benchmark
time may be accelerated by a scale factor:

`wall_time = run_start + (event_time - event_time_start) / scale_factor`

A standard benchmark run lasts 30 minutes of measured wall-clock time. For a
full one-week event-time replay, this corresponds to a scale factor of 336x.

## Data Dynamics

The benchmark distinguishes data by how it changes during a run:

- Static core data is loaded before the measured run and remains unchanged in
  the default workload. This includes exchanges, instruments, companies,
  sectors, identifier mappings, and pre-window fundamentals.
- Streamed event data is replayed during the run according to scaled event
  time. This includes market ticks, news/event updates, weather observations,
  and energy/grid observations.
- Update streams model data that can plausibly change within a week or arrive
  late. These include corrections to instrument mappings, revised context
  observations, late news-event links, and optional filing or metadata updates.
- Standing-query outputs are themselves streams or append/upsert tables emitted
  by the system under test. The driver records these outputs and validates them
  against the DuckDB oracle.

The following table is a placeholder for the benchmark's data-size and
throughput contract. Values should be filled from the committed data sources
and the selected run profile.

| Data Domain | Change Mode | Initial Size | Natural Throughput | Standard 30-Min Run Throughput | Notes |
|---|---|---:|---:|---:|---|
| Market ticks | Streamed events | TBD | TBD events/s | TBD events/s | High-volume DEBS replay; primary scale driver |
| Instrument and company metadata | Static core, optional updates | TBD rows | Static | Optional low-rate updates | Loaded before run |
| Company fundamentals | Static core, optional updates | TBD rows | Static | Optional low-rate updates | Default run uses pre-window facts |
| GDELT news documents | Streamed events plus historic context | TBD rows | TBD events/s | TBD events/s | Date-grain records may need deterministic intra-day spreading |
| GDELT event links | Streamed events plus historic context | TBD rows | TBD events/s | TBD events/s | Can arrive with or after documents |
| Electricity/grid observations | Streamed events | TBD rows | TBD events/s | TBD events/s | Hourly and 15-minute source grains |
| Weather observations | Streamed events | TBD rows | TBD events/s | TBD events/s | Sensor observations replayed by event time |
| Climate/emissions exposure | Static core or optional updates | TBD rows | Static | Optional low-rate updates | Planned data domain |
| Standing-query outputs | SUT output streams | Derived | Derived | Derived | Recorded by the driver for correctness checks |

## Workload Planes

The driver runs three workload planes concurrently:

1. Event replay:
   - market ticks as the high-volume stream,
   - news updates as a low-throughput contextual stream,
   - weather and energy/grid observations as time-series context,
   - selected update streams for data that may change within a week.

2. Standing-query result streams:
   - interval results such as 5-minute market bars,
   - 15-minute energy/weather/market views,
   - daily news and company summaries,
   - latest-state company or feed-health views.

   The system under test emits these standing-query results as output streams
   or append/upsert tables. The driver subscribes to or polls these outputs,
   records every emitted result with arrival time, and validates the recorded
   stream against the DuckDB oracle.

3. Ad hoc queries:
   - dashboard-style reads such as top movers, company profile, news pulse,
     zone pulse, rolling correlations, and feed health.

## Freshness And Deterministic Correctness

Each standing-query output and ad hoc query class has an event-time freshness
bound `F`. At benchmark logical time `t`, the required answer is the exact
result over all input records and update records with event time at most:

`t - F`

This makes validation deterministic. The system does not need to expose the
absolute latest result, but it must expose a result that is no more stale than
the freshness bound and exactly matches the DuckDB oracle at that snapshot.

For standing queries, correctness is checked over the recorded output stream.
Each emitted standing-query result must identify its logical output time or
window. The driver validates that:

- required output records are emitted,
- emitted records arrive within the freshness and latency bounds,
- emitted values match the DuckDB oracle for the corresponding snapshot,
- updates, corrections, or retractions are applied according to the query's
  declared output mode.

## Output Modes

Standing queries may expose results in different modes:

- append: each output interval produces immutable new rows,
- upsert: each output updates the latest value for a key,
- correction/retraction: later output records may revise or retract earlier
  results.

The driver records output-mode metadata so that correctness can be evaluated
deterministically.

## Metrics

The driver records:

- achieved input throughput,
- ingestion latency,
- standing-output latency,
- standing-output completeness,
- query latency for ad hoc/dashboard queries,
- freshness or staleness lag,
- correction latency for updates,
- correctness against DuckDB oracle snapshots,
- driver-side bottlenecks such as queueing and missed schedules.

The main benchmark metric is the maximum scale factor sustainable for a
30-minute measured run while satisfying throughput, freshness,
standing-output latency, ad hoc query-latency, and correctness requirements.

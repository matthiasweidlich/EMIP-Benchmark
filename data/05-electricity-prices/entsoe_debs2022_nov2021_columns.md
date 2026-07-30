# Column Descriptions — entsoe_debs2022_nov2021.csv

**Source:** ENTSO-E Transparency Platform (transparency.entsoe.eu)  
**Coverage:** Nov 8–14 2021 (Mon–Sun), Berlin time (CET = UTC+1)  
**Rows:** 672 (one per 15-minute interval, 96 per day × 7 days)  
**Columns:** 69 (63 original + 6 imbalance price columns merged from document type A85)  
**Note on forward-filling:** FR and NL generation data is published hourly by their TSOs; those columns are forward-filled to 15-min (four identical values per hour). DE/LU reports natively at 15-min. Day-ahead prices are hourly auction results — held constant across all 15-min intervals within the hour.  
**Note on FR imbalance granularity:** RTE (France) reports imbalance prices at 30-min resolution; the `imbalance_FR_*` columns are therefore null on every alternate 15-min row (336 non-null / 672 total). DE-LU and NL imbalance columns are fully populated at 15-min.

---

## Index

| # | Column | Unit | Description |
|---|---|---|---|
| 0 | `timestamp_berlin` | datetime (tz-aware) | Start of the 15-min interval in Europe/Berlin timezone (CET, UTC+1). E.g. `2021-11-08 00:00:00+01:00`. |

---

## Electricity prices (day-ahead auction)

Day-ahead prices are set the previous day in a single-price auction; the same price applies for the entire hour. Forward-filled to 15-min.

| # | Column | Unit | Description |
|---|---|---|---|
| 1 | `price_dayahead_DE_LU_EUR_MWh` | €/MWh | Day-ahead clearing price for the Germany/Luxembourg bidding zone (DE_LU). Covers continental Germany + Luxembourg (single zone since Oct 2018). Nov 2021 context: prices in this zone typically €50–100/MWh but spiked during the 2021 energy crisis. |
| 2 | `price_dayahead_FR_EUR_MWh` | €/MWh | Day-ahead price for France (FR). Nov 2021: significantly higher than Germany due to lower French nuclear availability (maintenance outages). Values like €172/MWh at midnight reflect the crisis peak. |
| 3 | `price_dayahead_NL_EUR_MWh` | €/MWh | Day-ahead price for Netherlands (NL). Often closely tracks Germany (adjacent zone, strong interconnection) but can diverge on congestion. Nov 2021: elevated (~€200/MWh) due to high gas generation costs (NL is gas-heavy). |

---

## Actual total load (demand / consumption)

Total electricity consumed within each bidding zone (net of pumped-storage consumption, losses etc.). Reflects economic activity, weather, time of day.

| # | Column | Unit | Description |
|---|---|---|---|
| 4 | `load_actual_DE_LU_MW` | MW | Actual total load in Germany+Luxembourg. ~48–75 GW on weekdays; drops ~10% on weekends. 15-min resolution. |
| 5 | `load_actual_FR_MW` | MW | Actual total load in France. ~50–80 GW. Hourly (forward-filled to 15-min). |
| 6 | `load_actual_NL_MW` | MW | Actual total load in Netherlands. ~10–15 GW. 15-min resolution. |

---

## Generation by source — Germany/Luxembourg (DE_LU)

Actual generation output by production type, 15-min resolution. "Aggregated" = total output fed into the grid; "Consumption" = self-consumption by the plant (e.g. pumped-storage pumping, or on-site use).

| # | Column | Unit | Description |
|---|---|---|---|
| 7 | `gen_DE_LU_Biomass_Actual_Aggregated_MW` | MW | Solid biomass and biogas plants. Relatively stable baseload (~4–5 GW). |
| 8 | `gen_DE_LU_Fossil_Brown_coal_Lignite_Actual_Aggregated_MW` | MW | Lignite (brown coal) plants. Germany's legacy baseload; high CO₂ intensity (~1.0 tCO₂/MWh). ~8–15 GW. Important for deriving grid carbon intensity. |
| 9 | `gen_DE_LU_Fossil_Gas_Actual_Aggregated_MW` | MW | Natural gas plants. Flexible; follows load/price signals. High in Nov 2021 due to elevated gas prices. |
| 10 | `gen_DE_LU_Fossil_Hard_coal_Actual_Aggregated_MW` | MW | Hard coal (bituminous coal) plants. Mid-merit order; ~0.85 tCO₂/MWh. |
| 11 | `gen_DE_LU_Fossil_Oil_Actual_Aggregated_MW` | MW | Oil-fired generation. Small (~200–300 MW); used for balancing. |
| 12 | `gen_DE_LU_Geothermal_Actual_Aggregated_MW` | MW | Geothermal. Very small and stable in Germany (~27 MW). |
| 13 | `gen_DE_LU_Hydro_Pumped_Storage_Actual_Aggregated_MW` | MW | Pumped-hydro generating (turbining): water released from upper reservoir to generate electricity. Positive = output to grid. |
| 14 | `gen_DE_LU_Hydro_Pumped_Storage_Actual_Consumption_MW` | MW | Pumped-hydro pumping: electricity consumed to pump water *up* to the reservoir. High at low-price / high-renewables periods (energy storage). Positive = consumed from grid. |
| 15 | `gen_DE_LU_Hydro_Run-of-river_and_poundage_Actual_Aggregated_MW` | MW | Run-of-river hydro: continuous generation proportional to river flow. Stable ~1 GW in Germany. |
| 16 | `gen_DE_LU_Hydro_Water_Reservoir_Actual_Aggregated_MW` | MW | Reservoir hydro (dispatchable). Small in Germany. |
| 17 | `gen_DE_LU_Nuclear_Actual_Aggregated_MW` | MW | Nuclear generation. Germany was phasing out nuclear; ~6–7 GW remaining in Nov 2021 (3 of 6 plants still online). Near-zero CO₂. Shutdown completed April 2023. |
| 18 | `gen_DE_LU_Other_Actual_Aggregated_MW` | MW | Other generation not classified above (mixed small sources). ~200–300 MW. |
| 19 | `gen_DE_LU_Other_renewable_Actual_Aggregated_MW` | MW | Other renewables (tidal, wave, small hydro, etc.). Small in Germany. |
| 20 | `gen_DE_LU_Other_renewable_Actual_Consumption_MW` | MW | Self-consumption of other renewables. Mostly empty in this dataset. |
| 21 | `gen_DE_LU_Solar_Actual_Aggregated_MW` | MW | Solar PV output. Near-zero at night and dawn/dusk in November; peaks midday ~5–10 GW on clear days. Key renewable-surge driver for negative prices. |
| 22 | `gen_DE_LU_Solar_Actual_Consumption_MW` | MW | Solar self-consumption (behind-the-meter). Near zero. |
| 23 | `gen_DE_LU_Waste_Actual_Aggregated_MW` | MW | Waste-to-energy (municipal solid waste, industrial waste). Stable baseload ~900 MW. |
| 24 | `gen_DE_LU_Wind_Offshore_Actual_Aggregated_MW` | MW | Offshore wind generation (North Sea / Baltic). Variable ~2–8 GW. Key driver of renewable share in DE. |
| 25 | `gen_DE_LU_Wind_Onshore_Actual_Aggregated_MW` | MW | Onshore wind. Germany's largest single generation source in Nov 2021; highly variable ~5–30+ GW. Primary driver of price volatility and negative-price events. |
| 26 | `gen_DE_LU_Wind_Onshore_Actual_Consumption_MW` | MW | Wind self-consumption. Near zero. |

---

## Generation by source — France (FR)

Hourly, forward-filled to 15-min. France is dominated by nuclear (~70% of generation).

| # | Column | Unit | Description |
|---|---|---|---|
| 27 | `gen_FR_Biomass_Actual_Aggregated_MW` | MW | Biomass generation in France. Small (~300–500 MW). |
| 28 | `gen_FR_Fossil_Gas_Actual_Aggregated_MW` | MW | Gas-fired generation. Elevated Nov 2021 (nuclear shortfall + high prices). |
| 29 | `gen_FR_Fossil_Hard_coal_Actual_Aggregated_MW` | MW | Coal plants. Small remaining capacity in France. |
| 30 | `gen_FR_Fossil_Oil_Actual_Aggregated_MW` | MW | Oil generation. Small, mostly island/backup plants. |
| 31 | `gen_FR_Hydro_Pumped_Storage_Actual_Aggregated_MW` | MW | Pumped-hydro generation output. France has significant pumped-hydro (Alps/Pyrenees). Blank = not reported. |
| 32 | `gen_FR_Hydro_Pumped_Storage_Actual_Consumption_MW` | MW | Pumped-hydro pumping consumption. |
| 33 | `gen_FR_Hydro_Run-of-river_and_poundage_Actual_Aggregated_MW` | MW | Run-of-river hydro. France has substantial river hydro (~3–5 GW). |
| 34 | `gen_FR_Hydro_Water_Reservoir_Actual_Aggregated_MW` | MW | Reservoir hydro. Dispatchable; significant in France. |
| 35 | `gen_FR_Hydro_Water_Reservoir_Actual_Consumption_MW` | MW | Reservoir hydro self-consumption. Mostly blank. |
| 36 | `gen_FR_Nuclear_Actual_Aggregated_MW` | MW | Nuclear generation. France's dominant source (~39–45 GW in Nov 2021, though reduced vs normal due to maintenance outages — the primary cause of FR's elevated prices vs DE). ~0 tCO₂/MWh. |
| 37 | `gen_FR_Solar_Actual_Aggregated_MW` | MW | Solar PV. Near zero at night; small even midday in November. |
| 38 | `gen_FR_Waste_Actual_Aggregated_MW` | MW | Waste-to-energy. Small (~250 MW). |
| 39 | `gen_FR_Wind_Onshore_Actual_Aggregated_MW` | MW | Onshore wind. France has growing capacity; variable ~1–8 GW. |

---

## Generation by source — Netherlands (NL)

15-min resolution. Netherlands is gas-dominated; significant offshore wind.

| # | Column | Unit | Description |
|---|---|---|---|
| 40 | `gen_NL_Biomass_Actual_Aggregated_MW` | MW | Biomass (co-firing in coal plants + dedicated). |
| 41 | `gen_NL_Biomass_Actual_Consumption_MW` | MW | Biomass self-consumption. Near zero. |
| 42 | `gen_NL_Fossil_Gas_Actual_Aggregated_MW` | MW | Gas generation. Netherlands' primary dispatchable source; elevated in Nov 2021 due to high TTF gas prices driving up NL electricity prices. |
| 43 | `gen_NL_Fossil_Gas_Actual_Consumption_MW` | MW | Gas plant self-consumption (auxiliary power). Small. |
| 44 | `gen_NL_Fossil_Hard_coal_Actual_Aggregated_MW` | MW | Coal generation. Several coal plants still operating in NL in 2021. |
| 45 | `gen_NL_Fossil_Hard_coal_Actual_Consumption_MW` | MW | Coal plant self-consumption. Small. |
| 46 | `gen_NL_Hydro_Run-of-river_and_poundage_Actual_Aggregated_MW` | MW | Run-of-river hydro. Negligible in NL (flat country). |
| 47 | `gen_NL_Hydro_Run-of-river_and_poundage_Actual_Consumption_MW` | MW | Self-consumption. Zero. |
| 48 | `gen_NL_Nuclear_Actual_Aggregated_MW` | MW | Nuclear. One plant (Borssele, ~480 MW). Stable near-constant output. |
| 49 | `gen_NL_Nuclear_Actual_Consumption_MW` | MW | Nuclear self-consumption. Near zero. |
| 50 | `gen_NL_Other_Actual_Aggregated_MW` | MW | Other generation (industrial CHP, waste heat, etc.). Variable; significant in NL due to large industrial sector. |
| 51 | `gen_NL_Other_Actual_Consumption_MW` | MW | Self-consumption of other generation. |
| 52 | `gen_NL_Solar_Actual_Aggregated_MW` | MW | Solar PV. Near zero at night; small in November. |
| 53 | `gen_NL_Solar_Actual_Consumption_MW` | MW | Solar self-consumption (behind-the-meter). Near zero. |
| 54 | `gen_NL_Waste_Actual_Aggregated_MW` | MW | Waste-to-energy. Netherlands has several large waste plants (~400 MW aggregate). |
| 55 | `gen_NL_Waste_Actual_Consumption_MW` | MW | Waste plant self-consumption. Small. |
| 56 | `gen_NL_Wind_Offshore_Actual_Aggregated_MW` | MW | Offshore wind (North Sea). NL has substantial offshore capacity ~1–2 GW in 2021; variable. |
| 57 | `gen_NL_Wind_Offshore_Actual_Consumption_MW` | MW | Offshore wind self-consumption. Near zero. |
| 58 | `gen_NL_Wind_Onshore_Actual_Aggregated_MW` | MW | Onshore wind. Variable ~200–700 MW in NL. |
| 59 | `gen_NL_Wind_Onshore_Actual_Consumption_MW` | MW | Onshore wind self-consumption. Near zero. |

---

## Cross-border physical flows

Net physical power flow between bidding zones (MW). Positive = export from the named zone.
Note: FR↔NL direct flows are absent — France and Netherlands are not electrically adjacent (power routes via Belgium or Germany); ENTSO-E does not report a direct FR↔NL cross-border series.

| # | Column | Unit | Description |
|---|---|---|---|
| 60 | `flow_DE_LU_to_FR_MW` | MW | Physical power export from Germany/Luxembourg to France. Positive = Germany exporting to France. In Nov 2021: Germany was exporting to France to compensate for France's nuclear shortfall. |
| 61 | `flow_FR_to_DE_LU_MW` | MW | Physical power export from France to Germany/Luxembourg. Positive = France exporting. Typically near zero when Germany is a net exporter. Both flows 60 & 61 can be non-zero simultaneously due to loop flows. |
| 62 | `flow_DE_LU_to_NL_MW` | MW | Physical power export from Germany/Luxembourg to Netherlands. Positive = Germany exporting. Germany is typically a significant exporter to NL. |
| 63 | `flow_NL_to_DE_LU_MW` | MW | Physical power export from Netherlands to Germany. Positive = NL exporting. Near zero when Germany exports to NL. |

---

## Derived columns useful for EMIT queries (not in the file — compute from above)

These are the silver-layer transforms your benchmark would compute:

| Derived column | Formula | Use |
|---|---|---|
| `carbon_DE_LU_gco2_per_kwh` | Σ(gen × emission_factor[fuel]) / Σ(gen) | Carbon intensity for scheduling queries |
| `carbon_FR_gco2_per_kwh` | Same, FR fuels | FR is low-carbon (nuclear-dominant) |
| `carbon_NL_gco2_per_kwh` | Same, NL fuels | NL is high-carbon (gas-dominant) |
| `renewables_share_DE_LU` | (Wind + Solar + Hydro) / total_gen | Renewable fraction signal |
| `total_gen_DE_LU_MW` | Sum of all gen_DE_LU_* Aggregated columns | Total generation for share computation |

Standard emission factors (tCO₂/MWh, approximate): Lignite 1.0, Hard coal 0.85, Gas 0.49, Oil 0.65, Biomass 0.23, Nuclear 0.012, Wind 0.011, Solar 0.045, Hydro 0.024.

---

## Context: Nov 2021 energy crisis signature in this data

This week sits in the middle of the **2021 European energy crisis** — making it valuable for robustness testing:
- **FR/NL prices are 2–4× higher than DE** (€172/200 vs €55 at midnight Nov 8) — a real cross-zone price divergence the scheduling queries must handle.
- **France's nuclear output is ~39 GW vs a normal ~50+ GW** — maintenance outages are visible in `gen_FR_Nuclear_*`.
- **DE wind is high** (~23–27 GW onshore on Nov 8 night) — driving DE prices down while FR/NL stay elevated, creating a strong Pareto frontier for carbon/cost-aware placement.
- **This is NOT yet the 2022 crisis peak** (€700+/MWh); it's a moderate crisis week — good for "normal vs stress" comparison when combined with a 2022 slice.

---

## Imbalance settlement prices (columns 64–69, ENTSO-E document type A85)

Actual post-delivery settlement prices applied to market parties who were
long or short in the balancing timeframe. More volatile than day-ahead prices
and directly reflects real-time supply/demand stress. DE-LU corresponds to the
German reBAP price. FR reports at 30-min resolution (nulls on alternate rows).

| # | Column | Unit | Description |
|---|---|---|---|
| 64 | `imbalance_DE_LU_long_EUR_MWh` | €/MWh | Long imbalance price for DE-LU: price paid to parties with a surplus in the settlement period. Fully populated at 15-min. |
| 65 | `imbalance_DE_LU_short_EUR_MWh` | €/MWh | Short imbalance price for DE-LU: price charged to parties with a deficit. Fully populated at 15-min. |
| 66 | `imbalance_FR_long_EUR_MWh` | €/MWh | Long imbalance price for France (RTE). **30-min resolution** — null on every other 15-min row. |
| 67 | `imbalance_FR_short_EUR_MWh` | €/MWh | Short imbalance price for France (RTE). **30-min resolution** — null on every other 15-min row. |
| 68 | `imbalance_NL_long_EUR_MWh` | €/MWh | Long imbalance price for Netherlands (TenneT NL). Fully populated at 15-min. |
| 69 | `imbalance_NL_short_EUR_MWh` | €/MWh | Short imbalance price for Netherlands (TenneT NL). Fully populated at 15-min. |

**Long vs short:** when the system has a surplus (more generation than load), the long price is paid out to surplus parties — it can go negative when renewables flood the grid. When the system is short (less generation than load), the short price is charged to deficit parties — it spikes during supply crunches. The spread between long and short widens under stress; a narrow spread indicates a balanced system.

**Robustness signal:** unlike the day-ahead price (set the day before), imbalance prices reflect what actually happened. Large divergence between `price_dayahead_*` and `imbalance_*_long/short` in the same interval indicates that the day-ahead market mispriced the hour — exactly the kind of signal a materialized-view maintenance workload should detect and react to.


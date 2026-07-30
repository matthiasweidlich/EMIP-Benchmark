# Source 4: GDELT / News Events

Raw public news and event signals. This source adds context that may explain or predict market movement.

## Pre-ETL Sample Tuples

| event_id | event_time | source_url | organization_text | theme | location | tone | salience |
|---|---|---|---|---|---|---:|---:|
| gdelt-001 | 2021-11-08T08:15:00Z | news.example/a | Shell | ENERGY;OIL;CLIMATE_POLICY | Netherlands | -1.8 | 0.72 |
| gdelt-002 | 2021-11-08T08:22:00Z | news.example/b | Airbus | AVIATION;EMISSIONS;EU_POLICY | France | -0.9 | 0.61 |
| gdelt-003 | 2021-11-08T08:40:00Z | news.example/c | Siemens Energy | RENEWABLES;GRID;HYDROGEN | Germany | 2.4 | 0.80 |
| gdelt-004 | 2021-11-08T09:05:00Z | news.example/d | ASML | SEMICONDUCTORS;SUPPLY_CHAIN | Netherlands | -2.2 | 0.76 |
| gdelt-005 | 2021-11-08T09:10:00Z | news.example/e | DAX companies | MARKETS;EUROPE;INFLATION | Germany | -1.1 | 0.55 |

## ETL Notes

- Resolve `organization_text` to canonical companies where possible.
- Split and classify semicolon-delimited themes.
- Deduplicate repeated stories or syndicated articles.
- Align events to market windows before and after publication time.
- Create `news_event`, `company_mention`, and `company_news_signal` tables.


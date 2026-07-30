# Source 6: Climate / Emissions Exposure

Raw facility or asset-level emissions exposure. This source supports transition-risk and climate-exposure materialized views.

## Pre-ETL Sample Tuples

| source | asset_id | owner_name | country | sector | technology | year | emissions_tco2e |
|---|---|---|---|---|---|---:|---:|
| climatetrace | asset-001 | Shell | NL | oil_and_gas | refinery | 2020 | 4200000 |
| epa_like | asset-002 | Airbus Operations SAS | FR | manufacturing | aircraft | 2020 | 930000 |
| climatetrace | asset-003 | Siemens AG | DE | industrials | electrical_equipment | 2020 | 610000 |
| climatetrace | asset-004 | ASML Holding NV | NL | semiconductors | chip_equipment | 2020 | 180000 |
| climatetrace | asset-005 | Unresolved Energy GmbH | DE | power | coal_generation | 2020 | 8700000 |

## ETL Notes

- Resolve `owner_name` to canonical company identifiers.
- Preserve unresolved assets for coverage and data-quality metrics.
- Normalize sectors and technologies into benchmark taxonomies.
- Aggregate facility emissions to company, country, sector, and year.
- Create `facility`, `facility_emission`, and `company_transition_exposure` tables.


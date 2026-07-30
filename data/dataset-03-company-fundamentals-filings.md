# Source 3: Company Fundamentals / Filings (ESEF)

Real annual-report fundamentals for the DEBS equity universe, built from
**ESEF filings** (European Single Electronic Format — the ESMA-mandated
Inline XBRL format for EU-regulated-market issuers). Identifier chain:
DEBS symbol → ISIN (`sym_isin.txt`) → **LEI** (GLEIF ISIN–LEI mapping) →
ESEF filings (via the [filings.xbrl.org](https://filings.xbrl.org) repository
of the XBRL International ESEF collection) → XBRL facts (xBRL-JSON).

## Files In This Repo (`03-company-fundamentals/`)

| File | Rows | Description |
|---|---|---|
| `esef_company_match.csv` | 2,090 ISIN links | LEI ↔ ISIN ↔ DEBS symbol ↔ Yahoo ticker crosswalk (73% of equity ISINs have an LEI) |
| `esef_filings.csv` | 868 | Selected filings: LEI, country, reporting period end, publication date, report/facts URLs |
| `esef_fundamentals.csv` | 26,501 | Long-format facts: one row per filing × IFRS concept × period × unit |
| `esef_fundamentals_sample100.csv` | 100 | Sample for quick inspection |
| `download_esef_fundamentals.py` | — | Reproducible pipeline (stdlib only; ~30–60 min full run) |

Coverage: **394 companies with filings** (of 1,892 DEBS-universe LEIs), 17
extracted metrics (revenue, net income, operating income, assets/liabilities/
equity breakdowns, operating cash flow, cash, EPS). Facts are consolidated
totals only (facts carrying extra XBRL dimensions are excluded).

## Sample Tuples (`esef_fundamentals.csv`)

| lei | company_name | filing_id | metric | value | unit | period_start | period_end | filing_published |
|---|---|---|---|---:|---|---|---|---|
| 724500Y6DUVHQD6OXN27 | ASML Holding N.V. | …-2021-12-31-ESEF-NL-0 | revenue | 13978500000 | EUR | 2020-01-01 | 2020-12-31 | 2022-03-16 |
| 724500Y6DUVHQD6OXN27 | ASML Holding N.V. | …-2021-12-31-ESEF-NL-0 | revenue | 18611000000 | EUR | 2021-01-01 | 2021-12-31 | 2022-03-16 |

## Timeline Caveats (important for benchmark semantics)

- ESEF became mandatory for fiscal years starting 2021 in most member states
  (COVID postponement), so the **first mandatory wave is FY2021, published
  spring 2022** — after the Nov 2021 benchmark week. FY2020 ESEF filings
  exist only for early adopters (101 of 868 filings).
- IFRS filings tag **prior-year comparatives**: FY2021 filings carry FY2020
  and FY2019 values. 393 of 394 companies have facts for periods ending
  before the benchmark week; those values were originally published in early
  2021 in non-XBRL form, so using them as static pre-window context is
  realistic even though the XBRL artifact appeared later. `filing_published`
  preserves the true publication date for point-in-time filtering.
- Filings with period ends through 2022-12-31 are included on purpose: they
  republish FY2021/FY2020 values and provide natural material for the
  optional filing/restatement update workloads.

## Known Gaps (kept as data-quality features)

- **No German filings**: the German OAM (Bundesanzeiger) does not contribute
  to the open filings.xbrl.org collection, so Xetra-listed German companies
  have no ESEF facts here. Coverage by filing country: FR 452, NL 185,
  AT 103, GB 50, others 78.
- Delisted/renamed companies (e.g. Royal Dutch Shell's 2021 ISIN) are missing
  from the *current* GLEIF ISIN–LEI file — the same identifier-drift problem
  as the Yahoo metadata in dataset 02.
- Amended filings appear as separate `filing_id`s (`…-0`, `…-1`); duplicate
  facts across filings are intentional (per-filing provenance).

## ETL Notes

- Join to instruments/companies via `esef_company_match.csv` (LEI ↔ ISIN ↔
  DEBS symbol); prefer LEI as the canonical company identifier.
- Values are as-tagged: mixed currencies (EUR, USD, GBP, DKK, SEK, …) and
  per-share units (`EUR/share`) — normalize units downstream.
- Same concept/period can appear in multiple filings (comparatives,
  amendments): deduplicate or version by `filing_published` when building
  `latest_company_fundamentals`-style views.

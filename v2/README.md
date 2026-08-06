# v2 — API-backed analysis pipeline

The next generation of this repo's analysis scripts. Instead of streaming the
389 MB `ln.data.1.AllData` flat file, these pull exactly the series they need
from the **BLS Public Data API v2** and cache them locally — zero large
downloads, and each script fixes the bugs catalogued for its legacy
counterpart in `../REVIEW_FINDINGS.md`.

The legacy pipeline in `../scripts/` is kept untouched as reference; the
catalog-driven tools there (`explore_ln.py`, the explorer builders, the
sum audit) still need the flat files, because the API has no catalog/search
endpoint.

## Setup

1. Get a free API key: <https://data.bls.gov/registrationEngine/>
2. Put it in a gitignored `.env` at the **repo root**:

   ```
   BLS_API_KEY=your-key-here
   ```

3. `pip install -r ../requirements.txt` (requests, pandas, matplotlib)

Every script runs from any working directory: `python v2/<script>.py`.

## Cache and query budget

- Responses are cached per series in `v2/cache/<ID>_<series-title>.json`
  (gitignored), e.g. `LNS12000000_seas-employment-level.json` — the title is
  the official one from the API's catalog metadata, so a directory listing
  reads like a series list.
- A series is refetched only if its cache was not written today **and** does
  not already contain the newest month a monthly release could have delivered
  (two calendar months back). `--refresh` on any script forces a refetch.
- Budget: the registered API tier allows 500 queries/day, 50 series/query,
  20 years/query. Fetching the **entire registry cold costs ~4 queries**
  (one 30-series batch x four 20-year windows, 1948-present). Warm cache
  costs **0** — every run prints
  `[bls_client] API queries this run: N (cache hits: M series)` so you can
  see it.

## Files

| File | Purpose |
| ---- | ------- |
| `bls_client.py` | API client, per-series cache, `.env` loader, output-path helper. `python v2/bls_client.py LNS12000000` smoke-tests it. |
| `series_registry.py` | Single source of truth: all 30 curated series IDs, the Jan-2026 break / Oct-2025 gap constants, the published population-control effect, and the helpers that enforce them. |
| `crosscheck_legacy.py` | Verifies v2 CSVs match the shipped legacy `../output/*.csv` month-for-month. |

Analyses (legacy provenance and the main fixes applied):

| Script | Replaces | Key fixes |
| ------ | -------- | --------- |
| `employment_by_sex.py` | `pull_employment_by_sex.py` + `employment_by_sex_clean.py` | Post-break segment starts **Jan-2026** (the legacy "clean" script started it Dec-2025, dragging the break step in and flipping the sign); segment marker column; no cross-break change columns by default; `--demo-subtraction` derives why subtracting the published effect double-counts (replaces `employment_by_sex_adjusted.py`, not ported). |
| `yoy_confirmation.py` | `yoy_confirmation.py` | End month defaults to latest matched pair; share suppressed on a near-zero adjusted base (the legacy defaults printed a meaningless 169%). |
| `pressure_test_men.py` | `pressure_test_men.py` | Clean exit on out-of-range baseline; gains largest-first; the fake Sep→Nov "MoM" over the Oct-2025 hole is masked. |
| `industry_by_sex.py` | `pull_industry_by_sex.py` | Kept its (correct) seam segmentation; fixed the broken break-month guard tuple. |
| `multiple_jobholders.py` | `multiple_jobholders_numbers.py` | Gap-aware 12-month average (windows touching Oct-2025 are NaN, `--allow-gap` to bridge); break-mixing windows flagged; CSV output added. |
| `nilf_charts.py` | `build_nilf_charts.py` | Chart 4 finally renders (the legacy guard waited on `LNS10000060`, which BLS never published — population has no SA form); share charts disclose their basis; per-line adjustment labels under `--sa`. |
| `verify_waterfall.py` | `verify_waterfall_measure.py` | Compares the six chart values numerically (PASS/FAIL, nonzero exit) instead of by eyeball; prints the -140k residual. |

Outputs land in `v2/output/` (tracked in git, like the legacy `output/`).

## Conventions (enforced, not assumed)

- **Never sum or difference across the Jan-2026 population-control break.**
  Windows are segmented at the seam; `series_registry.warn_if_crosses_break`
  fires when a user-requested window crosses it. The one sanctioned
  exception: matched-month NSA YoY with the published effect subtracted
  (`yoy_confirmation.py`), per BLS's own Table B procedure.
- **The Oct-2025 gap is a gap.** Diffs and rolling windows that span it are
  masked or flagged, never passed off as one-month/12-month figures.
- **`pivot`, never `pivot_table`** — duplicate observations raise instead of
  silently averaging. The client also hard-fails on duplicate
  (series_id, date) pairs.
- **Footnote codes survive the loader** — `check_break_footnote` warns if
  Jan-2026 rows stop carrying footnote 12 (constants drift canary).
- **Output paths never resolve against a data or cache directory**; defaults
  go to `v2/output/`, `-o` is honored as given.
- CSVs are written UTF-8 with BOM and ASCII headers so Excel on Windows
  renders them cleanly.

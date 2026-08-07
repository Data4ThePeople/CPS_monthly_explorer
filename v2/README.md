    # v2 — API-backed analysis pipeline

The next generation of this repo's analysis scripts. Instead of streaming the
389 MB `ln.data.1.AllData` flat file, these pull exactly the series they need
from the **BLS Public Data API v2** and cache them locally — zero large
downloads, and each script fixes the bugs catalogued for its legacy
counterpart in `../REVIEW_FINDINGS.md`.

The legacy pipeline in `../scripts/` is kept untouched as reference.
`explore_ln.py` and the sum audit there still need the 389 MB
`ln.data.1.AllData`. The explorer no longer does — `build_explorer.py` below
gets its values from the API and needs only the 15 MB `ln.series` catalog,
because the API has no catalog/search endpoint.

## Monthly refresh — run this on release morning

```
./v2/refresh.sh --publish
```

One command: checks whether BLS has actually published a new month, refreshes
the catalog, rebuilds the explorer, commits, pushes, deploys GitHub Pages, and
verifies the live file byte-for-byte. Drop `--publish` to build without
shipping. See [Refreshing the explorer](#refreshing-the-explorer) for what it
guards against and why a plain rebuild is not enough.

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
  (one 30-series batch x four 20-year windows, 1948-present). The explorer is
  the expensive one: its 2,151 series cost **~176 queries** cold. Warm cache
  costs **0** — every run prints
  `[bls_client] API queries this run: N (cache hits: M series)` so you can
  see it.

## Files

| File | Purpose |
| ---- | ------- |
| `bls_client.py` | API client, per-series cache, `.env` loader, output-path helper. `python v2/bls_client.py LNS12000000` smoke-tests it. |
| `series_registry.py` | Single source of truth: all 30 curated series IDs, the Jan-2026 break / Oct-2025 gap constants, the published population-control effect, and the helpers that enforce them. |
| `crosscheck_legacy.py` | Verifies v2 CSVs match the shipped legacy `../output/*.csv` month-for-month. |
| `build_explorer.py` | Builds the interactive explorer HTML. Catalog from `../data/ln.series`, values from the API. `--dry-run` prices the fetch before spending quota. |
| `explorer_template.html` | The themed page the explorer is rendered into; `__DATA__` is replaced with the payload. Edit here to change the look without touching Python. |
| `refresh.sh` | Monthly refresh: probe → catalog → rebuild → publish → verify. See above. |

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

## Refreshing the explorer

`v2/output/ln_explorer.html` is what the public embed serves:

<https://data4thepeople.github.io/CPS_monthly_explorer/v2/output/ln_explorer.html>

**A plain `build_explorer.py` rerun on release morning silently produces last
month's data.** The cache calls a series fresh while it holds data through
today minus two months, so on the August release morning a cache ending in
June still looks current and nothing is refetched — no error, no warning.
`--refresh` is mandatory, and `refresh.sh` is the reason this is hard to get
wrong. It:

1. **Probes before spending.** Compares the cached vs. live month on
   `LNS12000000` and stops if BLS has not posted yet (the API often trails the
   8:30am press release). `--force` overrides.
2. **Validates the catalog before replacing it.** Downloads `ln.series` to a
   temp file and checks line count and header, so a truncated response cannot
   leave you without a working catalog.
3. **Refuses to publish a stale build.** Re-reads the generated HTML and
   confirms its latest month matches what the API served.
4. **Deploys the way that works.** Push-triggered Pages builds on this repo
   hang; the script always triggers the build explicitly
   (`gh api -X POST repos/Data4ThePeople/CPS_monthly_explorer/pages/builds`),
   then polls the live URL and byte-compares it against the local file.

Save the catalog as `data/ln.series.txt` — `.gitignore` ignores that exact
name, and the 15 MB file must not be committed. `.nojekyll` at the repo root
is required for Pages to serve this repo at all.

Methodology prose for the public page lives in `../METHODOLOGY.md`; the
figures in it (2,151 series, 68,630 catalog rows, ~176 queries) come from a
build and should be re-checked when they change.

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

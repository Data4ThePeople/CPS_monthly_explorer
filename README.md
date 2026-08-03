# BLS LN (CPS) analysis

Analysis of the BLS **LN** series — the Current Population Survey (household
survey) — from the published flat files, plus CPS basic monthly microdata.

The governing rule in this repo: **every charted figure is exactly one
published BLS series**, never a sum or an average across series. The build
scripts enforce it rather than assume it.

## Layout

```
.
├── data/       Raw BLS flat files (ln.series, ln.data.*, ln.<dimension> maps)
├── scripts/    Analysis + build scripts (Python 3, one bash fetcher)
├── output/     Everything generated: CSVs, PNGs, HTML, console captures
└── README.md
```

Scripts resolve `data/` and `output/` **relative to the repo root**, so they run
correctly from any working directory:

```bash
python3 scripts/check_series_tail.py LNS11000003 6   # works from anywhere
```

Override with `--dir` (input) and `--out` (output) where a script exposes them.

## Getting the data

`data/` is mostly gitignored — the raw downloads are large and re-fetchable.
The small `ln.<dimension>` mapping files **are** tracked, because those are what
make the otherwise-opaque series IDs decodable.

Not tracked, fetch these yourself from
<https://download.bls.gov/pub/time.series/ln/>:

| File                     | Size   | What it is                                 |
| ------------------------ | ------ | ------------------------------------------ |
| `ln.data.1.AllData`      | ~389 MB | Every observation, every LN series         |
| `ln.series`              | ~15 MB  | The catalog: 68,630 series + dimension codes |

Save them into `data/`. A trailing `.txt` is fine — every script accepts either
`ln.series` or `ln.series.txt`.

> `ln.series` is the catalog of what exists. If a combination of dimensions has
> no row there, BLS does not publish it — which is why some intersections come
> up empty downstream.

CPS basic monthly microdata (separate dataset, only needed by `cps_extract.py`):

```bash
./scripts/fetch_cps.sh 2023 2026     # lands in data/cps/
```

## Scripts

**Catalog exploration** — what series exist, and are they populated?

| Script | Purpose |
| ------ | ------- |
| `explore_ln.py` | Explore the series catalog by dimension |
| `check_series_tail.py` | Last N observations of one series (is the final point real or partial?) |
| `inspect_raw_lines.py` | Raw lines with delimiters made visible, for layout debugging |
| `find_white_by_age.py` | Locate White-by-age series and confirm they have data |
| `find_primeage_by_race.py` | Prime-age (25–54) population series per race group |
| `pick_white_age_proof.py` | Narrow to the few series needed for the age-composition test |

**Analysis** — the Jan-2026 population-control break is the recurring hazard here.

| Script | Purpose |
| ------ | ------- |
| `pull_employment_by_sex.py` | Employment by sex since a baseline (default Dec-2023) |
| `employment_by_sex_adjusted.py` | Same, subtracting BLS's published population-control effect |
| `employment_by_sex_clean.py` | The defensible version: segments **at** the break, never sums across it |
| `pressure_test_men.py` | Monthly path behind the men's-employment finding, not just endpoints |
| `yoy_confirmation.py` | Jun-2025 → Jun-2026 matched-month change (seasonality cancels exactly) |
| `pull_industry_by_sex.py` | Employed by industry × sex, entirely within CPS (never mixing in CES) |
| `verify_waterfall_measure.py` | Is the redistribution waterfall population or labor force? |
| `multiple_jobholders_numbers.py` | Figures behind the multiple-jobholders chart (LNU02026625) |
| `cps_extract.py` | Prime-age LFPR by education × sex, from CPS microdata |

**Build / audit**

| Script | Purpose |
| ------ | ------- |
| `build_ln_explorer.py` | Self-contained interactive HTML explorer |
| `build_ln_explorer_themed.py` | Themed variant — **writes the same `output/ln_explorer.html`** |
| `build_nilf_charts.py` | The four not-in-labor-force post charts → `output/post_charts/` |
| `ur_by_occupation.py` | Unemployment rate by occupation → `output/ur_occ_output/` |
| `audit_alldata_sums.py` | Value-level reconciliation: does Men + Women = Both Sexes? |

## Notes

- `build_ln_explorer.py` and `build_ln_explorer_themed.py` are near-duplicates
  and write to the same output path, so whichever runs last wins. Worth merging
  behind a `--theme` flag.
- Dependencies are `pandas` and `matplotlib`; neither is currently installed in
  `.venv`.

## Data caveats

- **Jan-2026 population-control break.** Levels are not comparable across it.
  Prefer `employment_by_sex_clean.py`'s segmented treatment over subtracting the
  published effect — subtraction double-counts, as `employment_by_sex_adjusted.py`
  demonstrated.
- **No Oct-2025 CPS file exists** (appropriations lapse, no collection). The skip
  in `fetch_cps.sh` is correct, not a bug.
- **Two Jan-2026 CPS files exist.** `fetch_cps.sh` takes the corrected re-release.
- **CPS column positions changed in June 2024** (telework variables inserted), so
  `cps_extract.py` needs one Census data dictionary per layout era.

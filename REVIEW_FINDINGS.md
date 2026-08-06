# Code review findings

Full-repo review, 2026-08-05. Covers all 21 scripts, the generated outputs, the
tracked data files, and git history. **Nothing here has been fixed yet** — this
document records what was found and how to fix it.

Priorities at a glance (details below):

1. [F1](#f1) Segment-2 start date in `employment_by_sex_clean.py` — one line, flips a published-facing number
2. [F2](#f2) Reconcile `employment_by_sex_adjusted.py` with the README, remove its hardcoded headline
3. [F3](#f3) Small-denominator guard in `yoy_confirmation.py`
4. [F7](#f7) `out_path = folder / args.out` bug in five analysis scripts
5. [F6](#f6) `ur_by_occupation.py` unit-code defaults; [F5](#f5) chart-4 NSA fallback in `build_nilf_charts.py`
6. [F9](#f9) `fetch_cps.sh` `.csv`→`.dat` check; [F10](#f10) `cps_extract.py` duplicate-January guard
7. [F12](#f12) Merge the two explorer builders behind `--theme`

---

## A. Analytical correctness

### <a name="f1"></a>F1. `employment_by_sex_clean.py` — the "post-break" segment straddles the break (sign-flipping)

**Severity: highest in the repo.** The README holds this script up as the
defensible treatment ("segments **at** the break, never sums across it").
It doesn't. `SEAM = "2025-12"` is the last *pre*-break month
(`employment_by_sex_clean.py:53`), and Segment 2 runs `segment(…, seam, latest)`
(`employment_by_sex_clean.py:131-132`) — so the "post-break" segment starts on
the **old** population basis and contains the entire Jan-2026 break step, the
exact error the script exists to prevent. It contradicts the script's own
banner ("Never sum across the Jan-2026 seam", lines 118-119).

It is material, not cosmetic. From the shipped `output/employment_by_sex_clean.csv` (NSA):

| | As coded (Dec-25 → Jun-26) | Correct (Jan-26 → Jun-26) |
|---|---|---|
| Both sexes | **−998k** | **+1,052k** |
| Men | **−874k** | **+1,207k** |
| Women | −124k | −155k |

The sign of the post-break story flips for Both sexes and Men.

**Fix:** start Segment 2 at Jan-2026, i.e. pass `seam + 1 month` (or a
`POST_START = "2026-01"` constant) as the segment start on lines 131-132.
`pull_industry_by_sex.py:139-149` already does this correctly (`brk − 1 month`
as the pre-break endpoint, `brk` as the post-break start) — copy that pattern.
Also consider adding a break-marker column to the exported CSV (lines 134-139),
which currently spans the seam with no marker, so downstream charting
re-introduces the break the script segmented around.

### <a name="f2"></a>F2. `employment_by_sex_adjusted.py` — contradicts the README and its own arithmetic

- The README (Data caveats) says subtraction of the published
  population-control effect "double-counts, as `employment_by_sex_adjusted.py`
  demonstrated." The script contains no such demonstration — no double-count
  test, no comparison against the segmented result — and its closing block
  (lines 161-166) *recommends* the subtraction: "The apparent men's DECLINE in
  the raw SA series is a population-control artifact, not lost jobs."
- The closing headline "women's gain far exceeded men's" (line 163) is a
  **hardcoded string, not derived from the computed `adj` values**. Applying
  the script's own prescribed subtraction to the shipped data (NSA,
  Dec-2023 → Jun-2026) gives Men **+1,888k** vs Women **+1,513k** — the
  opposite of what it prints.
- No straddle guard: `--baseline 2026-03` would still subtract the full
  −1,588k men effect from an entirely post-break window, fabricating 1.6M men.
  (`yoy_confirmation.py:101-111` has the correct guard; this script doesn't.)
- Docstring (lines 21-24) claims it avoids crossing the NSA-measured effect
  into an SA window; line 106 does exactly that. The two bases give adjusted
  women's shares of 44.5% (NSA) vs 70.5% (SA) — printed side by side with no
  flag that the spread disqualifies the method.
- Unguarded division by `raw['Both sexes']` at lines 118-119 (the branch three
  lines up is guarded); hardcoded `+` sign at line 143 breaks if the constant's
  sign changes; internally inconsistent citations (line 8 "Feb-2026 Table B" vs
  line 11 "March 6, 2026 Table A" vs line 165 "Table A/B").

**Fix:** decide what this script is for. Either (a) demote it to an explicit
"here's why subtraction is wrong" demonstration — compute both the subtracted
and segmented answers and print the discrepancy — or (b) delete it and let the
README stop citing it. At minimum: delete the hardcoded headline (lines
161-166) or derive it from `adj`, add the straddle guard from
`yoy_confirmation.py`, and guard the division at 118-119. Then make the README
and the script tell the same story (see F16).

### <a name="f3"></a>F3. `yoy_confirmation.py` — prints a 169% share with its shipped defaults

The interpretation block (lines 132-139) tells the reader to check whether the
adjusted women's share "lands near the ~60% from the clean window." With the
shipped data and the default `--month 2026-06`: raw Both −1,161k, Men −1,774k,
Women +613k; adjusted Both **+271k** → women's share = **169%**, men's = −69%.
The near-zero adjusted denominator makes the share meaningless, and the
`!= 0` guard (line 124) doesn't catch it.

**Fix:** suppress the share when `abs(adjusted Both)` is below a materiality
threshold (e.g. 500k) and print the level changes instead, with a note that
the share is undefined on a near-zero base. Also: fall back to the latest
available month instead of hard-exiting when the default `--month` is absent
(line 99), and note that this script still performs the subtraction the README
declares invalid — resolve with F16.

### <a name="f4"></a>F4. `multiple_jobholders_numbers.py` — positional `rolling(12)` over a calendar with a hole

`d["ma12"] = d["value"].rolling(12).mean()` (line 86) is a 12-*observation*
window. October 2025 was never collected (confirmed by `ln.footnote.txt` codes
10/11 and the missing `2025-10` row in the shipped CSVs), so every recent
window spans **13 calendar months** — and also blends across the Jan-2026
population-control break — while the output labels it "12-MONTH MOVING
AVERAGE / trailing 12 months" (line 111). The most recent points, the ones
being quoted, are the affected ones. This is the only analysis script whose
docstring never mentions the break.

**Fix:** reindex to a monthly `DatetimeIndex` and use a date-aware window
(`rolling("366D", on="date")` or reindex + `min_periods=12`), or at minimum
assert date contiguity and print a warning when a window spans the Oct-2025
gap or the Jan-2026 seam. Also: `argparse(description=__doc__.splitlines()[1])`
(line 52) IndexErrors on a one-line docstring; the "NBER 2008-09 recession
window" comment (line 40) is wrong (the contraction ended June 2009 — the
band is fine as a peak-search window, the comment isn't); add a `-o` option so
the numbers behind a published chart aren't console-scrollback only.

### <a name="f5"></a>F5. `build_nilf_charts.py` — mixed seasonal adjustment inside ratios; chart 4 never renders

- **NSA numerator ÷ SA denominator.** On a default (NSA) run, chart 3 divides
  NSA `LNU05000000` (lines 196-197) by a denominator that always prefers SA
  `LNS10000000` (line 255). Chart 4 has the identical mismatch (lines 199-200
  vs 280). The chart-3 footer's claim of being the "mirror of the
  participation rate" is not exact with mismatched adjustment. Under `--sa`,
  chart 1 silently mixes two SA lines with one NSA line (`NILF_65` has no SA
  variant, line 198) with no per-line adjustment label. This cuts against the
  repo's own accuracy rule.
- **Chart 4 (`4_primeage_share.png`) is never produced** — the README promises
  four charts, disk has three. Chart 4's guard (line 280) tests the bare SA
  constant `LNS10000060`; there is no `POP_2554_NSA` constant and no `pick()`
  fallback, unlike chart 3's denominator (line 255). And if `nilf_25` itself is
  missing, the chart vanishes with no message at all (the skip note at lines
  301-304 only fires in an `elif`).

**Fix:** add `POP_2554_NSA = "LNU00000060"` and use `pick()` at line 280
(two lines — produces the fourth PNG); make each ratio use numerator and
denominator of the **same** adjustment basis, keyed off `args.sa`; label the
adjustment per line in chart 1's footer. Minor: guard `endlabel` against empty
series (lines 128-133), don't hardcode "of 10 candidates" (line 184) or the
`"(LNS10000060)"` string in the skip note, drop the unused `MO` list (58-59).

### <a name="f6"></a>F6. `ur_by_occupation.py` — cannot select any series (why `output/ur_occ_output/` doesn't exist)

`defaults = {d: series[d].mode().iloc[0] for d in dims}` (line 141) takes a
single global mode per dimension over the unfiltered catalog, then requires
every non-{occupation, lfst, periodicity} dimension at that default — 
**including the unit dims `tdat`/`pcts`** (lines 145-149). Levels vastly
outnumber rates, so the modal `tdat_code` is `00` (thousands); every
unemployment-**rate** series carries `01` (percent) and is excluded. The
selection comes back empty and the script dies — consistent with
`output/ur_occ_output/` not existing. This is exactly the failure mode
`build_ln_explorer.py`'s docstring documents as fixed (per-measure conditional
defaults, lines 200-207) — the fix never propagated here.

**Fix:** port the explorer's per-measure `tdat`/`pcts` defaults, and its
label-based `TOTAL_HINTS` defaults (lines 177-195 there — the comment says
mode-alone "caused a sex-baseline mismatch"). Take the mode over the monthly
subset, not the full catalog. Minor: `--out` help string is wrong (line 214,
says `<dir>`-relative); occupations lagging the global latest month are
silently dropped (lines 236-237); `NaN` ylim / zero-row subplot crashes when
`--start-year` postdates the data (lines 254-259); missing `plt.close(fig)`.

---

## B. Operational / CLI bugs

### <a name="f7"></a>F7. `-o`/`--out` is joined onto the *data* directory in five scripts

`pull_employment_by_sex.py:105`, `employment_by_sex_adjusted.py:158`,
`employment_by_sex_clean.py:138`, `pull_industry_by_sex.py:191`,
`pressure_test_men.py:105` all do `out_path = folder / args.out` where
`folder` is the **data** dir. It only appears to work because the default
`--out` is absolute (pathlib discards the left operand). Pass a relative
`-o out.csv` and the file lands in `data/`; pass `-o output/x.csv` and you get
`data/output/x.csv` → `FileNotFoundError`. This makes the README's "Override
with `--dir` (input) and `--out` (output)" false for these five.

**Fix:** use the pattern the build scripts already use
(`build_ln_explorer.py:152-153`, `audit_alldata_sums.py:124`):
`Path(args.out).expanduser()` resolved against `OUT_DIR` (or cwd) — never
against `--dir`. Add `out_path.parent.mkdir(parents=True, exist_ok=True)`
before writing.

### <a name="f8"></a>F8. Six scripts hardcode `ln.data.1.AllData.txt` (no un-suffixed fallback)

`check_series_tail.py:23`, `inspect_raw_lines.py:17`, `find_white_by_age.py:33`,
`find_primeage_by_race.py:24`, `pick_white_age_proof.py:28`,
`verify_waterfall_measure.py:23`. The README says "every script accepts
either" — and its own download table names the file **without** `.txt`, so
following the README breaks all six. `find_primeage_by_race.py` additionally
has no existence check at all (bare `FileNotFoundError`).
`multiple_jobholders_numbers.py:43-48` is the model: it tries both names, then
falls back to a glob.

**Fix:** copy that `find_data` helper into each script (or better, into a
shared module — see F11).

### <a name="f9"></a>F9. `fetch_cps.sh` — idempotency check tests for a file that never exists

- Line 25 skips a month when `${m}${yy}pub.csv` exists; the Census basic
  monthly zips contain **`.dat`** files (which is what `cps_extract.py:229`
  globs). No `.csv` ever appears, so **every run re-downloads and re-unzips
  every month**. Line 29's `echo "ok ${m}${yy}pub.csv"` names the wrong file
  too, as does the header comment (line 5).
- "ok" prints even when unzip fails: line 28 is `unzip -oq "$z" && rm -f "$z"`
  but line 29's echo is a separate unconditional statement.
- 404s leave zero-byte zips: `curl -f -o "$z"` creates the file before the
  status is known, and there's no `--remove-on-error`. Oct-2025 is a
  *permanent* expected 404, so a stray `oct25pub.zip` appears on every run.
- The README's claim that the script "takes the corrected Jan-2026 re-release"
  is an assumption about Census's server — the script just fetches the
  standard URL; the archive URL exists only in a comment (line 12) and nothing
  verifies which file was served.

**Fix:** test for `${m}${yy}pub.dat`; fold the echo into the `&&` chain (or
use `if unzip …; then … else echo "FAILED" >&2; fi`); add
`--remove-on-error --retry 3` to curl; log the served `Last-Modified` (or
byte size) for jan26 so the corrected-re-release claim is checkable.

### <a name="f10"></a>F10. `cps_extract.py` — two documented hazards it doesn't defend against

- **Duplicate Jan-2026.** The docstring (lines 36-38) warns two Jan-2026 files
  exist; the loop (line 235) concatenates every `*pub.dat` with no
  month-uniqueness check, so having both silently **double-weights January
  2026**. Fix: after parsing, assert one file per period (a
  `groupby("period")` file-count check) and exit with the offending filenames.
- **Dictionary collision keeps the oldest.** On a record-length collision with
  differing positions, `load_dictionaries` (lines 110-128) keeps the first
  file *alphabetically* — i.e. `cps_dd_2023.csv` beats `cps_dd_2024.csv`,
  the likely-wrong choice for later files — and only warns. Fix: make a
  genuine collision fatal, or key dictionaries by explicit date range instead
  of record length alone.
- Smaller: sanity-check runs on the raw frame but its message describes the
  filtered population (lines 152-153 vs docstring 30-32 — bounds and text
  disagree); `detect_reclen` trusts only the first line (131-135);
  `include_groups=False` (lines 210, 264) silently requires pandas ≥ 2.2,
  undeclared anywhere; `--out` into a missing directory fails only after the
  full parse (line 249 — mkdir first); `DATA_DIR` (line 50) is dead; the
  README's layout never mentions the required `dicts/` directory, and both
  input paths are required args, making this the clearest exception to the
  README's "runs from any cwd with repo-root defaults" claim.

### <a name="f11"></a>F11. Shared-loader duplication and the silent-averaging hazard

`load_data` is copy-pasted essentially verbatim in six analysis scripts. All
of them glob `folder.glob("ln.data*")` and concatenate **every** match, then
pivot with pandas' default `aggfunc="mean"`. If `ln.data.0.Current` ever sits
next to `ln.data.1.AllData` in `data/` (a normal BLS download pattern — the
README's layout line literally says `ln.data.*`), each month appears twice and
a revised value is silently **averaged with a stale one**. Relatedly, every
loader drops `footnote_codes`, discarding the one machine-readable signal for
the Jan-2026 break (footnote 12) and the Oct-2025 gap (footnotes 10/11) that
several scripts then re-hardcode as string constants.

**Fix:** extract one `scripts/_ln_common.py` with `load_data` (assert no
duplicate `(series_id, date)` pairs, or `drop_duplicates` keeping the newest
file), `find_data` (F8), and the repo-root path constants. Pass
`aggfunc="first"` or pre-assert uniqueness before any `pivot_table`. Keep the
footnote column through the loader.

---

## C. Explorer builders

### <a name="f12"></a>F12. `build_ln_explorer.py` vs `build_ln_explorer_themed.py` — confirmed trivial to merge

Verified: lines 1–469 are **byte-identical**; all four diff hunks sit inside
`HTML_TEMPLATE`; there are zero Python-logic differences (same selection
algorithm, packing, CLI, output path). The merge is: keep one file, extract
the palette/CSS into a `THEMES` dict (or a `__PALETTE__` JSON placeholder
alongside `__DATA__`), add `--theme`, delete ~700 duplicated lines. The only
wrinkle is four hex literals hardcoded in the JS
(`build_ln_explorer.py:637,649,651-652,657-658`) — the reason the fork touched
the JS at all — which the palette placeholder solves.

The themed fork also introduced two theme bugs to fix in the merge:

- `build_ln_explorer_themed.py:661` — the **SA** line still draws the
  light-theme teal `#085041` while the NSA paths (lines 663-664) use the
  parchment teal `#0a3d33`: two different teals on one chart.
- `build_ln_explorer_themed.py:513,520` — `.legend` and `.footer` kept the
  cool slate `#5b6763` on the warm parchment background (`.sub` was updated
  to `#6b5d3f`; these were missed).

Both files, smaller items: no `mkdir` before the final `write_text`
(line 463 — the only output writers in the repo without one); `--out` help
string and USAGE example claim `<dir>`/cwd-relative defaults (lines 29, 149 —
they're repo-root); the themed file's docstring still names
`build_ln_explorer.py` (lines 3, 28-29), so its `--help` reports the wrong
script; `json.dumps` output is inlined into a `<script>` tag unescaped
(line 462 — add `.replace("<", "\\u003c")`); `iterrows()` packing loop
(lines 407-410) is ~100× slower than a vectorized index computation;
duplicate `(year, month)` rows silently overwrite (401-412).

---

## D. Outputs, README, and repo hygiene

### <a name="f13"></a>F13. `employment_by_sex_adjusted.csv` and `employment_by_sex_clean.csv` are byte-identical

Both scripts export the same raw SA/NSA level panel; the "adjusted" arithmetic
exists only in console output. The adjusted CSV's filename oversells its
contents. **Fix:** either write the actually-adjusted columns to the adjusted
CSV, or stop writing a CSV from that script (it duplicates the clean one).
Note `output/employment_by_sex.csv`'s change columns are summed straight
across the Jan-2026 break — `pull_employment_by_sex.py` computes cross-break
changes with no warning and line 127 tells the user to chart them, which
contradicts the repo's own rule; add a break warning or refuse the default
window (resolve alongside F1/F16).

### <a name="f14"></a>F14. Git history contains a personal photo and a 15 MB catalog file

The initial commit (`edeea38`) included `HP7A0953_headshot.jpg` (a personal
headshot, ~205 KB) and `ln.series.txt` (68,631 lines); both were deleted in
`4545f7a` but remain fully recoverable from history. The GitHub repo
(`Data4ThePeople/CPS_monthly_explorer`) is currently **private**, so this is
low urgency — but **scrub history (`git filter-repo`) before ever flipping the
repo public**, and rotate the photo out of any other repos it may be in.

### <a name="f15"></a>F15. Cross-script inconsistencies (the same question answered differently)

- `check_series_tail.py:46-49` has a five-line comment explaining why
  prefix-matching series IDs is wrong; `inspect_raw_lines.py:38` does exactly
  that (`line.startswith(series_id)` matches `LNS11300003Q` when asked for
  `LNS11300003`). Fix: match on the exact tab-delimited field.
- `find_white_by_age.py` was written to detect catalog columns flexibly;
  `find_primeage_by_race.py:79-91` and `pick_white_age_proof.py:84-98`
  hardcode the column names instead. `find_primeage_by_race.py:97,127` reads a
  `seasonal` column that doesn't exist in `ln.series` (the other scripts
  derive it from `series_id[2]`), so `SA=` prints blank on every row.
- `pick_white_age_proof.py` claims to print "verified" series IDs (docstring
  line 18) but performs no data-availability check — `DATA_FILE` (line 28) is
  dead code. Its two siblings do check. Fix: add the AllData scan or soften
  the docstring.
- `find_white_by_age.py:161` — if `ln.race` is missing/renamed the White
  filter **silently disables itself** and dumps the full catalog (consistent
  with the 1.4 MB `white_by_age.txt` on disk). Fix: exit instead of warn when
  the race codes come back empty.
- The two documented selection fixes in `build_ln_explorer.py` propagated to
  `audit_alldata_sums.py` only partially (per-measure `tdat`/`pcts`: yes;
  label-based `TOTAL_HINTS` defaults: no) and to `ur_by_occupation.py` not at
  all (F6). `audit_alldata_sums.py:210-245` also hardcodes sex codes `"1"`/`"2"`
  despite loading `ln.sexs.txt`.
- `verify_waterfall_measure.py` never opens `ln.series`, never prints a title,
  and compares its six hardcoded chart values by eyeball only — the
  "verification" cannot fail programmatically. It's also all module-level code
  with no argparse or existence checks. Fix: resolve titles from the catalog,
  compare numerically, exit nonzero on mismatch; note the six waterfall values
  don't net to zero (−140k residual) — compute and print the residual.

### <a name="f16"></a>F16. README corrections needed

| README claim | Reality | Fix |
|---|---|---|
| Scripts resolve `data/`/`output/` repo-root-relative; run from any cwd | Inputs: true everywhere. Outputs: false for the five F7 scripts; `cps_extract.py` requires positional paths | Fix F7, document `cps_extract.py`'s args and the `dicts/` directory |
| "Override with `--dir` and `--out`" | Relative `--out` resolves against `--dir` in five scripts | F7 |
| "A trailing `.txt` is fine — every script accepts either" | False for the data file in six scripts (F8) | F8 |
| "Subtraction double-counts, as `employment_by_sex_adjusted.py` demonstrated" | The script demonstrates nothing of the sort and recommends the subtraction | F2; write the double-count demonstration down (in the README or the script) or drop the claim |
| "Prefer `employment_by_sex_clean.py`'s segmented treatment" | Right advice, but the recommended script has the F1 seam bug; `pull_industry_by_sex.py` is the one that segments correctly | F1 |
| `build_nilf_charts.py` makes "the four" post charts | Emits three; chart 4 unreachable | F5 |
| `ur_by_occupation.py` → `output/ur_occ_output/` | Directory absent; script can't select any series | F6 |
| "Dependencies … neither is currently installed in `.venv`" | No `.venv` exists in the checkout at all | Update or drop; consider a `requirements.txt` pinning pandas ≥ 2.2 (see F10) |
| "`fetch_cps.sh` takes the corrected re-release" | Unverified assumption about the Census server | F9 |
| "Every charted figure is exactly one published BLS series, never a sum or an average" | The multiple-jobholders chart's bold line is a computed 12-month average (within-series, so it dodges the letter of the rule); NILF charts 3/4 are ratios with mismatched adjustment | F4, F5; restate the rule to say what's actually intended (no cross-**series** arithmetic; within-series transforms disclosed) |

Stale `--help` strings contradicting the repo-root convention:
`explore_ln.py:320` ("default: current directory"), `ur_by_occupation.py:214`,
`build_ln_explorer.py:29,149`.

### <a name="f17"></a>F17. Minor / cosmetic (fix opportunistically)

- Dead constants: `OUT_DIR` in `yoy_confirmation.py:40`,
  `multiple_jobholders_numbers.py:36`, `explore_ln.py:59`; `DATA_DIR` in
  `cps_extract.py:50`; `DATA_FILE` in `pick_white_age_proof.py:28`. Unused
  imports: `re`/`glob` in `find_primeage_by_race.py:18-19`, `glob` in
  `pick_white_age_proof.py:23`. Dead `"seasonal"` entries in
  `build_ln_explorer.py:53` and `audit_alldata_sums.py:182-183`. Dead `rows`
  return in `pull_industry_by_sex.py:113-117,196`.
- `pull_industry_by_sex.py:146` — guard `if None not in (bL, mL, wL, b, ):`
  has a leftover trailing `b,` and omits the break-month values actually used
  on lines 147-149 (a missing Jan-2026 → `TypeError`). The docstring's
  "attempts finer health-specific children" is unimplemented (`CANDIDATES` is
  empty, lines 55-62). The `{err:+.0f}` format on line 126 signs an `abs()`.
- `pressure_test_men.py:110` — unguarded `men.loc[baseline]` (`KeyError` on an
  out-of-range `--baseline`; sibling scripts exit cleanly). Line 123
  `ranked.tail(4)` prints "biggest gains" smallest-first. The Jan-2026
  annotation only appears if the month makes the top-6 drops table.
- `pull_employment_by_sex.py`: `--nsa` doesn't change the default output
  filename (silently overwrites the SA CSV, line 80); em-dash column headers
  + UTF-8-no-BOM = mojibake in Excel on Windows (line 101); baseline
  filter-before-check ordering (lines 92-94).
- `check_series_tail.py:83` — `is_rate = max(abs(v)) < 1000` misformats any
  level series under 1M persons as a rate. `n_tail=0` returns the whole series
  (line 66).
- `explore_ln.py:307-310` — the `<--` flag marker fires on almost every row
  and breaks column alignment; `pd.to_numeric(None)` TypeError path at
  line 148; `engine="python"` on a 15 MB read here and in three other scripts
  (~10× slower than the C engine for no benefit).
- `audit_alldata_sums.py`: empty-`rows` `KeyError` at lines 313-315; four bare
  `next(...)` StopIterations at 138-142; docstring omits
  `sum_check_summary.csv` (line 28), the larger of its two outputs.

#!/usr/bin/env python3
"""
build_ln_explorer.py -- Build a self-contained interactive HTML explorer for
monthly BLS LN (CPS) series.

THE ACCURACY GUARANTEE
Every chart shown is exactly ONE published BLS series -- never a sum, never
an average. The build enforces this:
  * A (dimension, value) pair qualifies only if a MONTHLY series exists where
    that dimension is off-default and EVERY other dimension sits at its
    catalog default (16 years and over, both sexes, all races, ...).
  * Each dimension also offers its own default as the FIRST Group option
    (Age -> "16 years and over", Race -> "All Races", ...) when the default
    label is meaningful (not "N/A"). That option maps to the headline
    all-defaults series -- still exactly one published series.
  * tdat/pcts (unit descriptors) are pinned per-measure, not globally, so
    rates (which carry a percent unit code) are not wrongly excluded.
  * If several candidates remain (SA vs NSA, current vs discontinued), one is
    chosen deterministically: currently-published first, then seasonally
    adjusted, then longest history. Duplicates are logged, never blended.
  * The chart footer displays the exact BLS series ID being plotted, so any
    reader can verify the numbers at bls.gov.

The optional 4th dropdown (sex) appears only when a series exists that is
identical to the current selection except sex -- same one-series rule.

USAGE:
  python3 build_ln_explorer.py -d ~/Desktop/ln
  python3 build_ln_explorer.py -d ~/Desktop/ln --exclude indy occupation --out ln_explorer.html

Requires: pandas. Inputs: ln.series, ln.* mapping files, ln.data.1.AllData
(.txt suffixes fine). Output: one HTML file, embed-ready.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

SKIP_FILES = {"ln.series", "ln.txt", "ln.contacts", "ln.footnote"}

# Dimensions that are measure/format descriptors, not demographic cuts:
# never shown in the picker. tdat/pcts are additionally pinned per-measure.
NON_PICKER = {"lfst", "periodicity", "tdat", "pcts", "seasonal"}

FRIENDLY = {
    "born": "Nativity", "sexs": "Sex", "ages": "Age", "race": "Race",
    "orig": "Hispanic origin", "education": "Education",
    "mari": "Marital status", "vets": "Veteran status",
    "disa": "Disability status", "cert": "Certification / license",
    "mjhs": "Multiple jobholders", "class": "Class of worker",
    "indy": "Industry", "occupation": "Occupation", "occ": "Occupation",
    "duration": "Duration of unemployment", "look": "Reason for unemployment",
    "rnlf": "Job search (not in labor force)", "wkst": "Work schedule status",
    "hour": "Hours worked", "chld": "Presence of children",
    "absn": "Absence status", "rjnw": "Reason for absence from work",
    "rwns": "Reason for part-time work", "seek": "Job seeker status",
    "jdes": "Want a job", "expr": "Work experience",
    "entr": "Labor force entrant", "hheader": "Family head",
    "activity": "Activity", "tlwk": "Telework",
}
MEASURE_PRIORITY = ["civilian labor force", "employed", "employment",
                    "unemployed", "unemployment", "unemployment rate",
                    "labor force participation rate",
                    "employment-population ratio", "not in labor force"]
NOTE_DIMS = ["ages", "sexs", "race", "orig"]  # shown as fixed-filter note


def base_name(p: Path) -> str:
    n = p.name
    return n[:-4] if n.lower().endswith(".txt") else n


def find_file(folder: Path, name: str):
    for cand in (name, name + ".txt", name + ".TXT"):
        if (folder / cand).exists():
            return folder / cand
    return None


def read_bls(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False,
                     na_values=[], engine="python")
    df.columns = [c.strip() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    return df


def load_lookups(folder: Path) -> dict:
    lookups = {}
    for f in sorted(folder.iterdir()):
        name = base_name(f)
        if (not name.startswith("ln.") or name in SKIP_FILES
                or name.startswith("ln.data")):
            continue
        try:
            t = read_bls(f)
        except Exception:
            continue
        cc = [c for c in t.columns if c.endswith("_code")]
        tc = [c for c in t.columns if c.endswith("_text")]
        if len(cc) == 1 and tc:
            lookups[cc[0]] = dict(zip(t[cc[0]], t[tc[0]]))
    return lookups


def match_lookup(lookups, dim_col):
    if dim_col in lookups:
        return lookups[dim_col]
    pre = dim_col.replace("_code", "")
    for k, v in lookups.items():
        kp = k.replace("_code", "")
        if kp.startswith(pre) or pre.startswith(kp):
            return v
    return {}


def pick_one(cands: pd.DataFrame) -> pd.Series:
    """Deterministic choice among duplicate candidates: currently published
    first, then seasonally adjusted, then longest history, then series_id."""
    c = cands.copy()
    c["_end"] = pd.to_numeric(c["end_year"], errors="coerce").fillna(0)
    c["_sa"] = (c["seasonal"] == "S").astype(int)
    c["_len"] = c["_end"] - pd.to_numeric(c["begin_year"],
                                          errors="coerce").fillna(9999)
    c = c.sort_values(["_end", "_sa", "_len", "series_id"],
                      ascending=[False, False, False, True])
    return c.iloc[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("-d", "--dir", default=".")
    ap.add_argument("--data", help="explicit path to ln.data file")
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="dimension names to leave out of the picker "
                         "(e.g. --exclude indy occupation)")
    ap.add_argument("--out", default=None,
                    help="output HTML path (default <dir>/ln_explorer.html)")
    args = ap.parse_args()
    folder = Path(args.dir).expanduser()
    out_path = (Path(args.out).expanduser() if args.out
                else folder / "ln_explorer.html")

    sp = find_file(folder, "ln.series")
    if sp is None:
        sys.exit(f"ERROR: no ln.series(.txt) in {folder}")
    series = read_bls(sp)
    if "seasonal" not in series.columns:
        series["seasonal"] = series["series_id"].str[2]
    lookups = load_lookups(folder)

    dims = [c for c in series.columns
            if c.endswith("_code") and c != "footnote_codes"]
    short = {d: d.replace("_code", "") for d in dims}
    per_dim = next(d for d in dims if short[d].startswith("periodicity"))
    lfst_dim = next(d for d in dims if short[d].startswith("lfst"))
    sexs_dim = next((d for d in dims if short[d].startswith("sex")), None)

    monthly = series[series[per_dim] == "M"].copy()

    # Defaults: prefer the code whose LABEL is an explicit universe total
    # (e.g. "Both Sexes", "16 years and over", "All Races", "All Origins",
    # "N/A"). Fall back to the most common code only when no such label
    # exists. Mode alone is unsafe: in a filtered subset the most frequent
    # value can be a non-total (this caused a sex-baseline mismatch).
    TOTAL_HINTS = ("both sexes", "16 years and over", "all races",
                   "all origins", "all educational levels", "all industries",
                   "all occupations", "n/a", "number in thousands",
                   "total", "all persons")

    def pick_default(d):
        lk = match_lookup(lookups, d)
        present = set(monthly[d].unique())
        # exact-ish label match against known totals, restricted to codes
        # that actually appear in the monthly data
        for code, txt in lk.items():
            if code in present and txt.strip().lower() in TOTAL_HINTS:
                return code
        # substring fallback (e.g. "16 years and over" variants)
        for code, txt in lk.items():
            if code in present and any(h in txt.strip().lower()
                                       for h in TOTAL_HINTS):
                return code
        return monthly[d].mode().iloc[0]

    defaults = {d: pick_default(d) for d in dims}
    lfst_lk = match_lookup(lookups, lfst_dim)

    # tdat/pcts describe the MEASURE'S unit (thousands vs percent): their
    # default must be conditional on the measure, or rate series would be
    # wrongly rejected for not matching "Number in thousands".
    measure_dims = [d for d in dims if short[d] in ("tdat", "pcts")]
    cond_default = {}
    for d in measure_dims:
        cond_default[d] = monthly.groupby(lfst_dim)[d].agg(
            lambda s: s.mode().iloc[0])

    picker_dims = [d for d in dims
                   if short[d] not in NON_PICKER
                   and short[d] not in set(args.exclude)
                   and (monthly[d] != defaults[d]).any()]

    ages_dim = next((d for d in dims if short[d].startswith("age")), None)

    def off_default_count(df, exclude=()):
        """Count dimensions off their default, optionally ignoring some
        dimensions (e.g. ages, whose universe varies by breakdown)."""
        cnt = pd.Series(0, index=df.index)
        for d in dims:
            if d in (lfst_dim, per_dim) or d in exclude:
                continue
            if d in measure_dims:
                expected = df[lfst_dim].map(cond_default[d])
                cnt += (df[d] != expected).astype(int)
            else:
                cnt += (df[d] != defaults[d]).astype(int)
        return cnt

    # Off-default count ignoring age -- used to find each dimension's series
    # regardless of which age universe BLS publishes it at.
    monthly["_offN"] = off_default_count(monthly)
    monthly["_offNa"] = off_default_count(monthly, exclude=(ages_dim,)) \
        if ages_dim else monthly["_offN"]

    def age_universe(d):
        """The single age code that IS this dimension's universe: among
        series off-default only on {d, ages}, the most common age code.
        Falls back to the global age default."""
        if not ages_dim:
            return None
        cand = monthly[(monthly["_offNa"] == 1)
                       & (monthly[d] != defaults[d])]
        if cand.empty:
            return defaults.get(ages_dim)
        return cand[ages_dim].mode().iloc[0]

    def others_at_default(df, free):
        """Boolean mask: every dimension NOT in `free` equals its default
        (measure dims use their per-measure conditional default). `free`
        is the set of dimensions allowed to vary (e.g. {d, ages_dim, sexs}).
        lfst and periodicity are always free. This EXACT-MATCH rule replaces
        off-default counting, so no extra off-default dim can leak in."""
        mask = pd.Series(True, index=df.index)
        for dd in dims:
            if dd in free or dd in (lfst_dim, per_dim):
                continue
            if dd in measure_dims:
                mask &= df[dd] == df[lfst_dim].map(cond_default[dd])
            else:
                mask &= df[dd] == defaults[dd]
        return mask

    wanted = {}   # series_id -> seasonal
    dupes = 0

    def reg(chosen) -> str:
        wanted[chosen["series_id"]] = chosen["seasonal"]
        return chosen["series_id"]

    # Headline series (ALL dims at defaults), one per measure. These back the
    # "default" Group option of every dimension.
    headline = {}
    for lf, cand in monthly[monthly["_offN"] == 0].groupby(lfst_dim):
        chosen = pick_one(cand)
        dupes += len(cand) - 1
        headline[lf] = chosen

    # Sex first-level series, one per (measure, sex). These back both the
    # Sex dimension itself and the sex drilldown of default Group options.
    sexs_first = {}
    if sexs_dim:
        sf = monthly[(monthly["_offN"] == 1)
                     & (monthly[sexs_dim] != defaults[sexs_dim])]
        for (lf, sx), cand in sf.groupby([lfst_dim, sexs_dim]):
            chosen = pick_one(cand)
            dupes += len(cand) - 1
            sexs_first[(lf, sx)] = chosen

    combos, dim_meta, measures_used = {}, [], set()

    for d in picker_dims:
        lk = match_lookup(lookups, d)
        if d == ages_dim:
            au = defaults.get(ages_dim)
        else:
            au = age_universe(d)

        # free dims for the BASE (no sex) series: this dim + ages
        free_base = {d}
        if ages_dim:
            free_base.add(ages_dim)
        base_pool = monthly[(monthly[d] != defaults[d])
                            & others_at_default(monthly, free_base)]
        # For non-age dims, pin ages to this dimension's universe so we don't
        # mix universes. For the age dim, ages is the picker (leave it free).
        if d != ages_dim and ages_dim:
            base_pool = base_pool[base_pool[ages_dim] == au]

        # sex sub-variant pool: additionally free sexs
        sub_pool = None
        if sexs_dim and d != sexs_dim:
            free_sex = set(free_base) | {sexs_dim}
            sub_pool = monthly[(monthly[d] != defaults[d])
                              & (monthly[sexs_dim] != defaults[sexs_dim])
                              & others_at_default(monthly, free_sex)]
            if d != ages_dim and ages_dim:
                sub_pool = sub_pool[sub_pool[ages_dim] == au]

        vals, cmb = [], {}
        for code, grp in base_pool.groupby(d):
            entry = {}
            for lf, cand in grp.groupby(lfst_dim):
                chosen = pick_one(cand)
                dupes += len(cand) - 1
                entry[lf] = {"i": reg(chosen)}
                measures_used.add(lf)
            if sub_pool is not None:
                sub = sub_pool[sub_pool[d] == code]
                for (lf, sx), cand in sub.groupby([lfst_dim, sexs_dim]):
                    if lf not in entry:
                        continue
                    chosen = pick_one(cand)
                    dupes += len(cand) - 1
                    entry[lf].setdefault("x", {})[sx] = reg(chosen)
            if entry:
                vals.append({"code": code, "label": lk.get(code, code)})
                cmb[code] = entry
        vals.sort(key=lambda v: v["code"])

        # The dimension's own default as the first Group option
        # (e.g. Age -> "16 years and over"), backed by headline series.
        dlab = lk.get(defaults[d], "")
        if dlab and dlab.strip().upper() != "N/A" and headline:
            entry = {}
            for lf, chosen in headline.items():
                e = {"i": reg(chosen)}
                if sexs_dim and d != sexs_dim:
                    x = {sx: reg(ch) for (lf2, sx), ch in sexs_first.items()
                         if lf2 == lf}
                    if x:
                        e["x"] = x
                entry[lf] = e
                measures_used.add(lf)
            if entry:
                vals.insert(0, {"code": defaults[d], "label": dlab})
                cmb[defaults[d]] = entry

        if vals:
            for code, entry in cmb.items():
                combos[f"{short[d]}|{code}"] = entry
            dim_meta.append({"key": short[d],
                             "label": FRIENDLY.get(short[d], short[d]),
                             "ageUniverse": (match_lookup(lookups, ages_dim)
                                             .get(au, "") if ages_dim else ""),
                             "values": vals})

    dim_meta.sort(key=lambda m: m["label"])
    # Open the tool on Age by default: move the age dimension to the front so
    # it is the first (selected) option when the explorer loads.
    dim_meta.sort(key=lambda m: (m["key"] != "ages", m["label"]))
    print(f"Picker dimensions: {len(dim_meta)} | value groups: "
          f"{len(combos)} | series to embed: {len(wanted)} | "
          f"duplicate candidates resolved deterministically: {dupes}")

    # ---- stream data file for the wanted series ----
    paths = [Path(args.data)] if args.data else sorted(folder.glob("ln.data*"))
    if not paths:
        sys.exit(f"ERROR: no ln.data.* file in {folder}")
    frames = []
    for p in paths:
        print(f"Streaming {p.name} ...")
        for chunk in pd.read_csv(p, sep="\t", dtype=str, chunksize=1_000_000,
                                 keep_default_na=False, na_values=[]):
            chunk.columns = [c.strip() for c in chunk.columns]
            chunk["series_id"] = chunk["series_id"].str.strip()
            hit = chunk[chunk["series_id"].isin(wanted)]
            if len(hit):
                frames.append(hit)
    if not frames:
        sys.exit("ERROR: selected series not found in data file(s).")
    data = pd.concat(frames, ignore_index=True)
    data["period"] = data["period"].str.strip()
    data = data[data["period"].str.match(r"M(0[1-9]|1[0-2])$")]
    data["value"] = pd.to_numeric(data["value"].str.strip(), errors="coerce")
    data["year"] = pd.to_numeric(data["year"].str.strip(), errors="coerce")
    data["month"] = data["period"].str[1:].astype(int)
    data = data.dropna(subset=["value", "year"])

    packed = {}
    for sid, g in data.groupby("series_id"):
        g = g.sort_values(["year", "month"])
        y0, m0 = int(g["year"].iloc[0]), int(g["month"].iloc[0])
        idx0 = y0 * 12 + (m0 - 1)
        n = int(g["year"].iloc[-1]) * 12 + (g["month"].iloc[-1] - 1) - idx0 + 1
        vals = [None] * int(n)
        for _, r in g.iterrows():
            vals[int(r["year"]) * 12 + int(r["month"] - 1) - idx0] = (
                int(r["value"]) if float(r["value"]).is_integer()
                else round(float(r["value"]), 1))
        packed[sid] = {"id": sid, "s": wanted[sid], "y0": y0, "m0": m0,
                       "v": vals}

    # prune anything whose data never showed up
    n_missing = 0
    for key in list(combos):
        entry = combos[key]
        for lf in list(entry):
            if entry[lf]["i"] not in packed:
                del entry[lf]
                n_missing += 1
                continue
            x = entry[lf].get("x")
            if x:
                for sx in list(x):
                    if x[sx] not in packed:
                        del x[sx]
                if not x:
                    del entry[lf]["x"]
        if not entry:
            del combos[key]
    if n_missing:
        print(f"WARNING: pruned {n_missing} combo entries with no data rows")
    for m in dim_meta:
        m["values"] = [v for v in m["values"]
                       if f"{m['key']}|{v['code']}" in combos]
    dim_meta = [m for m in dim_meta if m["values"]]

    measures = {lf: lfst_lk.get(lf, lf) for lf in sorted(measures_used)}

    def mprio(lf):
        lab = measures[lf].lower()
        for i, m in enumerate(MEASURE_PRIORITY):
            if m in lab:
                return (i, lab)
        return (len(MEASURE_PRIORITY), lab)

    measure_order = sorted(measures, key=mprio)
    fixed_defaults = []
    for nd in NOTE_DIMS:
        col = next((d for d in dims if short[d] == nd), None)
        if col:
            lab = match_lookup(lookups, col).get(defaults[col], "")
            if lab and lab.upper() != "N/A":
                fixed_defaults.append([nd, lab])
    sexs_labels = (match_lookup(lookups, sexs_dim) if sexs_dim else {})

    payload = {"dims": dim_meta, "combos": combos, "series": packed,
               "measures": measures, "measureOrder": measure_order,
               "fixedDefaults": fixed_defaults, "sexLabels": sexs_labels}
    blob = json.dumps(payload, separators=(",", ":"))
    html = HTML_TEMPLATE.replace("__DATA__", blob)
    out_path.write_text(html, encoding="utf-8")
    print(f"\nWrote {out_path}  ({out_path.stat().st_size/1e6:.1f} MB)")
    print("Open it in a browser; embed as-is in Prismic.")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CPS Explorer &mdash; Data 4 The People</title>
<style>
:root{--teal:#0a3d33;--coral:#712B13;--paper:#f2e9d0;--gold:#9a7b2e;
--ink:#2b2317;--line:#cdbb96;--parch:#efe4c6;--parch2:#e7d8b3}
*{box-sizing:border-box}
body{margin:0;color:var(--ink);
background:
 radial-gradient(120% 80% at 20% 0%, #f4ecd6 0%, #efe4c6 55%, #e7d6ac 100%),
 repeating-linear-gradient(0deg, rgba(120,90,40,0.020) 0 2px, transparent 2px 4px);
background-blend-mode:multiply;
font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:980px;margin:0 auto;padding:20px 16px 28px}
.eyebrow{font-size:11px;letter-spacing:.22em;color:var(--gold);
text-transform:uppercase;font-weight:700;font-family:Georgia,serif}
h1{font-family:Georgia,'Times New Roman',serif;color:var(--teal);
font-size:clamp(20px,3.6vw,29px);margin:.2em 0 .1em;line-height:1.18;
font-weight:700;letter-spacing:.01em}
h1::first-letter{color:var(--coral)}
.sub{color:#6b5d3f;font-size:13px;margin-bottom:14px;font-style:italic;font-family:Georgia,serif}
.controls{display:flex;flex-wrap:wrap;gap:10px 14px;margin-bottom:14px}
.ctrl{display:flex;flex-direction:column;gap:3px;min-width:150px;flex:1}
.ctrl label{font-size:11px;font-weight:700;letter-spacing:.12em;
text-transform:uppercase;color:var(--gold);font-family:Georgia,serif}
select{appearance:none;-webkit-appearance:none;color:var(--ink);
background-color:#f7efd9;
border:1.5px solid var(--gold);border-radius:7px;padding:9px 30px 9px 11px;
font-size:14px;width:100%;font-family:Georgia,serif;
box-shadow:inset 0 1px 0 rgba(255,255,255,0.5),0 1px 2px rgba(90,70,30,0.12);
background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6'><path d='M0 0l5 6 5-6z' fill='%239a7b2e'/></svg>");
background-repeat:no-repeat;background-position:right 11px center}
select:focus{outline:3px solid rgba(154,123,46,.35)}
#sexWrap.hidden{display:none}
.chartbox{background:linear-gradient(180deg,#faf3df 0%,#f4ead0 100%);
border:1px solid var(--gold);border-radius:10px;
padding:12px 10px 6px;position:relative;
box-shadow:0 1px 0 rgba(255,255,255,0.6) inset,0 2px 10px rgba(90,70,30,0.12)}
.chartbox::before{content:"";position:absolute;inset:5px;border:1px solid rgba(154,123,46,0.4);border-radius:7px;pointer-events:none}
svg text{font:11px Georgia,"Times New Roman",serif;fill:#6b5d3f}
.tip{position:absolute;pointer-events:none;background:#2b2317;color:#f2e9d0;
padding:6px 9px;border-radius:5px;font-size:12px;line-height:1.35;
white-space:nowrap;transform:translate(-50%,-115%);display:none;z-index:5;
font-family:Georgia,serif;border:1px solid var(--gold)}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:#5b6763;
margin:8px 2px 2px}
.legend span::before{content:"";display:inline-block;width:18px;height:3px;
margin-right:5px;vertical-align:middle;border-radius:2px}
.lg-raw::before{background:var(--teal);opacity:.35}
.lg-ma::before{background:var(--teal)}
.lg-sa::before{background:var(--teal)}
.footer{margin-top:12px;font-size:12px;color:#5b6763;display:flex;
flex-wrap:wrap;gap:8px 16px;align-items:center}
.chip{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
background:var(--teal);color:#f2e9d0;padding:2px 8px;border-radius:4px;
font-size:12px;letter-spacing:.03em}
.badge{border:1px solid var(--gold);color:var(--gold);border-radius:5px;
padding:1px 7px;font-size:11px;font-weight:700}
.src{color:var(--gold);font-size:11.5px;margin-top:8px}
@media(max-width:560px){
 .wrap{padding:14px 11px 22px}
 .ctrl{min-width:100%;flex:1 1 100%}
 .controls{gap:8px}
 h1{font-size:20px}
 .sub{font-size:12px}
 select{font-size:16px;padding:10px 30px 10px 11px}
 .chartbox{padding:8px 4px 4px}
 .footer{font-size:11px;gap:6px 10px}
 .chip{font-size:11px}
 .src{font-size:10.5px}
 svg text{font-size:10px}
 .tip{font-size:13px;padding:7px 10px}
}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head><body><div class="wrap">
<div class="eyebrow">Data 4 The People &middot; CPS Monthly Explorer</div>
<h1 id="title">&nbsp;</h1>
<div class="sub" id="subtitle">&nbsp;</div>
<div class="controls">
 <div class="ctrl"><label for="dimSel">Dimension</label>
  <select id="dimSel" aria-label="Choose dimension"></select></div>
 <div class="ctrl"><label for="valSel">Group</label>
  <select id="valSel" aria-label="Choose group"></select></div>
 <div class="ctrl"><label for="lfsSel">Measure</label>
  <select id="lfsSel" aria-label="Choose measure"></select></div>
 <div class="ctrl hidden" id="sexWrap"><label for="sexSel">Sex</label>
  <select id="sexSel" aria-label="Choose sex"></select></div>
</div>
<div class="chartbox"><svg id="chart" role="img"
 aria-label="Time series chart"></svg><div class="tip" id="tip"></div></div>
<div class="legend" id="legend"></div>
<div class="footer">
 <span>Series&nbsp;<span class="chip" id="sid"></span></span>
 <span class="badge" id="seas"></span>
 <span id="range"></span>
</div>
<div class="src">Source: U.S. Bureau of Labor Statistics, Current Population
Survey (LN database). One published BLS series per view &mdash; no values are
combined or averaged. Chart: Data 4 The People.</div>
</div>
<script>
const DB=__DATA__;
const $=id=>document.getElementById(id);
const dimSel=$("dimSel"),valSel=$("valSel"),lfsSel=$("lfsSel"),
sexSel=$("sexSel"),sexWrap=$("sexWrap"),svg=$("chart"),tip=$("tip");
const MO=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
function opt(sel,items,keep){const old=keep?sel.value:null;sel.innerHTML="";
 for(const[v,t]of items){const o=document.createElement("option");
  o.value=v;o.textContent=t;sel.appendChild(o);}
 if(old&&[...sel.options].some(o=>o.value===old))sel.value=old;}
function dimObj(){return DB.dims.find(d=>d.key===dimSel.value);}
function comboKey(){return dimSel.value+"|"+valSel.value;}
function measureObj(){return (DB.combos[comboKey()]||{})[lfsSel.value];}
function currentEntry(){
 const m=measureObj();if(!m)return null;
 let sid=m.i;
 if(!sexWrap.classList.contains("hidden")&&sexSel.value&&m.x
    &&m.x[sexSel.value])sid=m.x[sexSel.value];
 return DB.series[sid];}
function fillDims(){opt(dimSel,DB.dims.map(d=>[d.key,d.label]));}
function fillVals(){opt(valSel,dimObj().values.map(v=>[v.code,v.label]),true);}
function fillMeasures(){
 const avail=DB.combos[comboKey()]||{};
 opt(lfsSel,DB.measureOrder.filter(m=>avail[m])
   .map(m=>[m,DB.measures[m]]),true);}
function fillSex(){
 if(dimSel.value==="sexs"){sexWrap.classList.add("hidden");return;}
 const m=measureObj();
 const found=m&&m.x?Object.keys(m.x):[];
 if(!found.length){sexWrap.classList.add("hidden");return;}
 sexWrap.classList.remove("hidden");
 const items=[["",(DB.fixedDefaults.find(f=>f[0]==="sexs")||["","All"])[1]]]
   .concat(found.sort().map(c=>[c,DB.sexLabels[c]||c]));
 opt(sexSel,items,true);}
function isPct(){const l=(DB.measures[lfsSel.value]||"").toLowerCase();
 return l.includes("rate")||l.includes("ratio")||l.includes("percent");}
function fmt(v){if(v==null)return"\u2013";
 return isPct()?v.toFixed(1)+"%":v.toLocaleString("en-US");}
function ma12(v){const out=new Array(v.length).fill(null);
 for(let i=11;i<v.length;i++){let s=0,ok=true;
  for(let j=i-11;j<=i;j++){if(v[j]==null){ok=false;break}s+=v[j];}
  if(ok)out[i]=s/12;}return out;}
function draw(){
 const e=currentEntry();if(!e){svg.innerHTML="";return;}
 const dim=dimObj(),val=dim.values.find(v=>v.code===valSel.value);
 const sexOn=!sexWrap.classList.contains("hidden")&&sexSel.value;
 $("title").textContent=DB.measures[lfsSel.value]+" \u2014 "+val.label+
   (sexOn?", "+DB.sexLabels[sexSel.value]:"");
 const note=DB.fixedDefaults.filter(f=>f[0]!==dim.key).map(f=>{
   if(f[0]==="sexs"&&sexOn)return DB.sexLabels[sexSel.value];
   // if this dimension has its own age universe, show it in place of 16+
   if(f[0]==="ages"&&dim.ageUniverse)return dim.ageUniverse;
   return f[1];});
 $("subtitle").textContent=note.join(" \u00b7 ")+
   (isPct()?"":" \u00b7 Thousands of persons")+" \u00b7 Monthly, "+
   (e.s==="S"?"seasonally adjusted":"not seasonally adjusted");
 $("sid").textContent=e.id;
 $("seas").textContent=e.s==="S"?"SA":"NSA";
 const n=e.v.length,y1=e.y0+Math.floor((e.m0-1+n-1)/12),
   m1=(e.m0-1+n-1)%12;
 $("range").textContent=MO[e.m0-1]+" "+e.y0+" \u2013 "+MO[m1]+" "+y1;
 $("legend").innerHTML=e.s==="S"
  ?'<span class="lg-sa">Seasonally adjusted monthly value</span>'
  :'<span class="lg-raw">Monthly (NSA)</span><span class="lg-ma">12-month moving average</span>';
 // --- geometry (mobile: taller aspect ratio so a narrow chart isn't squashed) ---
 const W=svg.parentNode.clientWidth-16;
 const mob=W<500;
 const H=mob?Math.max(280,Math.min(360,W*0.85)):Math.max(300,Math.min(430,W*.45));
 svg.setAttribute("viewBox","0 0 "+W+" "+H);
 svg.setAttribute("width",W);svg.setAttribute("height",H);
 const L=mob?46:58,R=mob?10:14,T=12,B=30,pw=W-L-R,ph=H-T-B;
 const vals=e.v.filter(v=>v!=null);
 let lo=Math.min(...vals),hi=Math.max(...vals);
 if(lo===hi){lo-=1;hi+=1}
 const pad=(hi-lo)*.07;lo=Math.max(0,lo-pad);hi+=pad;
 const X=i=>L+pw*i/(n-1||1),Y=v=>T+ph*(1-(v-lo)/(hi-lo));
 let g="";
 const step=niceStep((hi-lo)/5);
 for(let t=Math.ceil(lo/step)*step;t<=hi;t+=step){
  g+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(t)+'" y2="'+Y(t)+
   '" stroke="#d8c9a0"/>'+
   '<text x="'+(L-7)+'" y="'+(Y(t)+4)+'" text-anchor="end">'+
   (isPct()?t.toFixed(step<1?1:0)+"%":t.toLocaleString())+"</text>";}
 const yrSpan=y1-e.y0,every=yrSpan>50?10:yrSpan>20?5:yrSpan>8?2:1;
 for(let yr=Math.ceil(e.y0/every)*every;yr<=y1;yr+=every){
  const i=(yr-e.y0)*12+(1-e.m0);if(i<0||i>n-1)continue;
  g+='<text x="'+X(i)+'" y="'+(H-8)+'" text-anchor="middle">'+yr+"</text>";}
 const path=(arr)=>{let d="",pen=false;
  for(let i=0;i<n;i++){const v=arr[i];
   if(v==null){pen=false;continue}
   d+=(pen?"L":"M")+X(i).toFixed(1)+" "+Y(v).toFixed(1);pen=true;}return d;}
 if(e.s==="S"){
  g+='<path d="'+path(e.v)+'" fill="none" stroke="#085041" stroke-width="2.2"/>';
 }else{
  g+='<path d="'+path(e.v)+'" fill="none" stroke="#0a3d33" stroke-width="1.1" opacity="0.30"/>';
  g+='<path d="'+path(ma12(e.v))+'" fill="none" stroke="#0a3d33" stroke-width="2.4"/>';
 }
 const series=e.s==="S"?e.v:ma12(e.v);
 for(let i=n-1;i>=0;i--){if(series[i]!=null){
  g+='<circle cx="'+X(i)+'" cy="'+Y(series[i])+
   '" r="4" fill="#712B13"/><text x="'+(X(i)-8)+'" y="'+
   (Y(series[i])-9)+'" text-anchor="end" style="fill:#712B13;font-weight:700">'+
   fmt(isPct()?series[i]:Math.round(series[i]))+"</text>";break;}}
 svg.innerHTML=g;
 const showAt=(clientX,clientY)=>{
  const r=svg.getBoundingClientRect();
  // scale from CSS px to viewBox coords (SVG width may differ from render width)
  const sx=W/r.width;
  const i=Math.round(((clientX-r.left)*sx-L)/pw*(n-1));
  if(i<0||i>n-1||(e.v[i]==null&&ma12(e.v)[i]==null)){tip.style.display="none";return;}
  const mIdx=(e.m0-1+i)%12,yr=e.y0+Math.floor((e.m0-1+i)/12);
  const m=ma12(e.v)[i];
  tip.innerHTML="<b>"+MO[mIdx]+" "+yr+"</b><br>"+fmt(e.v[i])+
   (e.s==="U"&&m!=null?"<br>12-mo avg: "+fmt(isPct()?m:Math.round(m)):"");
  tip.style.left=((clientX-r.left))+"px";
  tip.style.top=((clientY-r.top))+"px";tip.style.display="block";};
 svg.onmousemove=ev=>showAt(ev.clientX,ev.clientY);
 svg.onmouseleave=()=>tip.style.display="none";
 // touch: drag a finger across the chart to scrub the tooltip
 const touch=ev=>{if(ev.touches&&ev.touches[0]){
   showAt(ev.touches[0].clientX,ev.touches[0].clientY);ev.preventDefault();}};
 svg.ontouchstart=touch;svg.ontouchmove=touch;
 svg.ontouchend=()=>setTimeout(()=>{tip.style.display="none";},1400);
}
function niceStep(x){const p=Math.pow(10,Math.floor(Math.log10(x)));
 const f=x/p;return(f<1.5?1:f<3.5?2:f<7.5?5:10)*p;}
dimSel.onchange=()=>{fillVals();fillMeasures();fillSex();draw();};
valSel.onchange=()=>{fillMeasures();fillSex();draw();};
lfsSel.onchange=()=>{fillSex();draw();};
sexSel.onchange=draw;
window.onresize=draw;
fillDims();fillVals();fillMeasures();fillSex();draw();
</script></body></html>"""


if __name__ == "__main__":
    main()

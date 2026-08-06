#!/usr/bin/env python3
"""Build the self-contained interactive HTML explorer for monthly LN series.

API port of scripts/build_ln_explorer_themed.py. The legacy build needed two
downloads: ln.series (the catalog) AND ln.data.1.AllData (~389 MB of every
observation BLS publishes). Only the catalog half is irreplaceable -- the BLS
API has no catalog endpoint, so ln.series is still required to know which
series exist and which dimension combination each ID encodes. The 389 MB
observation file is not: those values come through bls_client instead, cached
per series, so a rebuild after the first run costs zero API queries.

THE ACCURACY GUARANTEE (unchanged from the legacy build)
Every chart shown is exactly ONE published BLS series -- never a sum, never an
average. A (dimension, value) pair qualifies only if a MONTHLY series exists
where that dimension is off-default and EVERY other dimension sits at its
catalog default. Where several candidates remain (SA vs NSA, current vs
discontinued) one is chosen deterministically and the duplicates are logged,
never blended. The chart footer shows the exact series ID being plotted.

Quota: ~2,150 series qualify. At 50 series/query x 4 twenty-year windows
(1948->now) that is ~176 queries against a 500/day registered limit. Series
are fetched in chunks and cached as each chunk lands, so an exhausted quota
costs only the unfetched remainder -- rerun the next day to resume.

Run from anywhere:
    python v2/build_explorer.py --dry-run          # query cost, no fetching
    python v2/build_explorer.py
    python v2/build_explorer.py --exclude indy occupation -o explorer.html
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bls_client

V2_DIR = bls_client.V2_DIR
DATA_DIR = bls_client.REPO_ROOT / "data"
TEMPLATE = V2_DIR / "explorer_template.html"

CATALOG_URL = "https://download.bls.gov/pub/time.series/ln/ln.series"
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

TOTAL_HINTS = ("both sexes", "16 years and over", "all races",
               "all origins", "all educational levels", "all industries",
               "all occupations", "n/a", "number in thousands",
               "total", "all persons")


# --------------------------------------------------------------------------
# catalog (ln.series + the small ln.* mapping files)

def base_name(p: Path) -> str:
    n = p.name
    return n[:-4] if n.lower().endswith(".txt") else n


def find_file(folder: Path, name: str) -> Path | None:
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


def match_lookup(lookups: dict, dim_col: str) -> dict:
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


def build_catalog(folder: Path, exclude: list[str]) -> dict:
    """Derive the picker metadata and the set of series to embed from
    ln.series. Returns dims/combos/measures plus `wanted` (id -> seasonal)."""
    sp = find_file(folder, "ln.series")
    if sp is None:
        sys.exit(
            f"ERROR: no ln.series(.txt) in {folder}\n"
            "The BLS API has no catalog endpoint, so the explorer cannot be\n"
            "built without it. Download it (15 MB, gitignored) with:\n"
            f"  curl -A '<your email>' -o {folder / 'ln.series.txt'} {CATALOG_URL}"
        )
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
    # (e.g. "Both Sexes", "16 years and over"). Mode alone is unsafe: in a
    # filtered subset the most frequent value can be a non-total.
    def pick_default(d):
        lk = match_lookup(lookups, d)
        present = set(monthly[d].unique())
        for code, txt in lk.items():
            if code in present and txt.strip().lower() in TOTAL_HINTS:
                return code
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
                   and short[d] not in set(exclude)
                   and (monthly[d] != defaults[d]).any()]

    ages_dim = next((d for d in dims if short[d].startswith("age")), None)

    def off_default_count(df, drop=()):
        cnt = pd.Series(0, index=df.index)
        for d in dims:
            if d in (lfst_dim, per_dim) or d in drop:
                continue
            if d in measure_dims:
                expected = df[lfst_dim].map(cond_default[d])
                cnt += (df[d] != expected).astype(int)
            else:
                cnt += (df[d] != defaults[d]).astype(int)
        return cnt

    monthly["_offN"] = off_default_count(monthly)
    monthly["_offNa"] = (off_default_count(monthly, drop=(ages_dim,))
                         if ages_dim else monthly["_offN"])

    def age_universe(d):
        """The single age code that IS this dimension's universe: among series
        off-default only on {d, ages}, the most common age code."""
        if not ages_dim:
            return None
        cand = monthly[(monthly["_offNa"] == 1)
                       & (monthly[d] != defaults[d])]
        if cand.empty:
            return defaults.get(ages_dim)
        return cand[ages_dim].mode().iloc[0]

    def others_at_default(df, free):
        """Every dimension NOT in `free` equals its default. This EXACT-MATCH
        rule replaces off-default counting, so no extra off-default dim can
        leak in."""
        mask = pd.Series(True, index=df.index)
        for dd in dims:
            if dd in free or dd in (lfst_dim, per_dim):
                continue
            if dd in measure_dims:
                mask &= df[dd] == df[lfst_dim].map(cond_default[dd])
            else:
                mask &= df[dd] == defaults[dd]
        return mask

    wanted: dict[str, str] = {}
    dupes = 0

    def reg_series(chosen) -> str:
        wanted[chosen["series_id"]] = chosen["seasonal"]
        return chosen["series_id"]

    # Headline series (ALL dims at defaults), one per measure.
    headline = {}
    for lf, cand in monthly[monthly["_offN"] == 0].groupby(lfst_dim):
        headline[lf] = pick_one(cand)
        dupes += len(cand) - 1

    # Sex first-level series, one per (measure, sex).
    sexs_first = {}
    if sexs_dim:
        sf = monthly[(monthly["_offN"] == 1)
                     & (monthly[sexs_dim] != defaults[sexs_dim])]
        for (lf, sx), cand in sf.groupby([lfst_dim, sexs_dim]):
            sexs_first[(lf, sx)] = pick_one(cand)
            dupes += len(cand) - 1

    combos, dim_meta, measures_used = {}, [], set()

    for d in picker_dims:
        lk = match_lookup(lookups, d)
        au = defaults.get(ages_dim) if d == ages_dim else age_universe(d)

        free_base = {d}
        if ages_dim:
            free_base.add(ages_dim)
        base_pool = monthly[(monthly[d] != defaults[d])
                            & others_at_default(monthly, free_base)]
        # Pin ages to this dimension's universe so universes never mix.
        if d != ages_dim and ages_dim:
            base_pool = base_pool[base_pool[ages_dim] == au]

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
                entry[lf] = {"i": reg_series(pick_one(cand))}
                dupes += len(cand) - 1
                measures_used.add(lf)
            if sub_pool is not None:
                sub = sub_pool[sub_pool[d] == code]
                for (lf, sx), cand in sub.groupby([lfst_dim, sexs_dim]):
                    if lf not in entry:
                        continue
                    entry[lf].setdefault("x", {})[sx] = reg_series(pick_one(cand))
                    dupes += len(cand) - 1
            if entry:
                vals.append({"code": code, "label": lk.get(code, code)})
                cmb[code] = entry
        vals.sort(key=lambda v: v["code"])

        # The dimension's own default as the first Group option, backed by
        # the headline (all-defaults) series -- still exactly one series.
        dlab = lk.get(defaults[d], "")
        if dlab and dlab.strip().upper() != "N/A" and headline:
            entry = {}
            for lf, chosen in headline.items():
                e = {"i": reg_series(chosen)}
                if sexs_dim and d != sexs_dim:
                    x = {sx: reg_series(ch)
                         for (lf2, sx), ch in sexs_first.items() if lf2 == lf}
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

    # Open the tool on Age: sort it to the front so it loads selected.
    dim_meta.sort(key=lambda m: (m["key"] != "ages", m["label"]))

    measures = {lf: lfst_lk.get(lf, lf) for lf in sorted(measures_used)}

    def mprio(lf):
        lab = measures[lf].lower()
        for i, m in enumerate(MEASURE_PRIORITY):
            if m in lab:
                return (i, lab)
        return (len(MEASURE_PRIORITY), lab)

    fixed_defaults = []
    for nd in NOTE_DIMS:
        col = next((d for d in dims if short[d] == nd), None)
        if col:
            lab = match_lookup(lookups, col).get(defaults[col], "")
            if lab and lab.upper() != "N/A":
                fixed_defaults.append([nd, lab])

    return {
        "dims": dim_meta,
        "combos": combos,
        "measures": measures,
        "measureOrder": sorted(measures, key=mprio),
        "fixedDefaults": fixed_defaults,
        "sexLabels": match_lookup(lookups, sexs_dim) if sexs_dim else {},
        "wanted": wanted,
        "dupes": dupes,
    }


# --------------------------------------------------------------------------
# observations (BLS API via bls_client, replacing ln.data.1.AllData)

def estimate_queries(n_series: int, end_year: int) -> int:
    """Queries a full fetch would cost: one per (batch of 50, 20-year window)."""
    span = end_year - bls_client.EARLIEST_YEAR + 1
    batches = -(-n_series // bls_client.MAX_SERIES_PER_QUERY)
    windows = -(-span // bls_client.MAX_YEARS_PER_QUERY)
    return batches * windows


def fetch_observations(wanted: dict[str, str], chunk: int,
                       refresh: bool) -> pd.DataFrame:
    """Fetch every wanted series, one chunk at a time. bls_client writes its
    cache at the end of each fetch call, so chunking makes an interrupted or
    quota-exhausted run resumable: completed chunks are already on disk."""
    ids = list(wanted)
    frames = []
    for i in range(0, len(ids), chunk):
        batch = ids[i:i + chunk]
        n = i + len(batch)
        print(f"  [{n:>5}/{len(ids)}] fetching {len(batch)} series ...",
              flush=True)
        try:
            frames.append(bls_client.fetch(batch, refresh=refresh))
        except bls_client.BLSAPIError as e:
            if not frames:
                raise
            print(
                f"\nERROR after {i} series: {e}\n"
                "Series fetched so far ARE cached -- rerun this command to "
                "resume from here (cached series cost no queries).",
                file=sys.stderr,
            )
            sys.exit(1)
    return pd.concat(frames, ignore_index=True)


def pack(data: pd.DataFrame, wanted: dict[str, str]) -> dict:
    """Pack tidy observations into the explorer's dense monthly encoding:
    {id, s, y0, m0, v} where v[k] is the value k months after y0-m0."""
    packed = {}
    d = data.copy()
    d["year"] = d["date"].dt.year
    d["month"] = d["date"].dt.month
    # sort=True (the default) emits series in series_id order, so a rebuild is
    # byte-reproducible and diffable against a previous build.
    for sid, g in d.groupby("series_id"):
        g = g.sort_values(["year", "month"])
        y0, m0 = int(g["year"].iloc[0]), int(g["month"].iloc[0])
        idx0 = y0 * 12 + (m0 - 1)
        last = int(g["year"].iloc[-1]) * 12 + int(g["month"].iloc[-1]) - 1
        vals: list = [None] * (last - idx0 + 1)
        for y, m, v in zip(g["year"], g["month"], g["value"]):
            vals[int(y) * 12 + int(m) - 1 - idx0] = (
                int(v) if float(v).is_integer() else round(float(v), 1))
        packed[sid] = {"id": sid, "s": wanted[sid], "y0": y0, "m0": m0,
                       "v": vals}
    return packed


def prune(cat: dict, packed: dict) -> int:
    """Drop combo entries whose series returned no observations, then drop
    values and dimensions left empty. Returns the number pruned."""
    combos, n_missing = cat["combos"], 0
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
    for m in cat["dims"]:
        m["values"] = [v for v in m["values"]
                       if f"{m['key']}|{v['code']}" in combos]
    cat["dims"] = [m for m in cat["dims"] if m["values"]]
    return n_missing


# --------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Build the interactive LN explorer HTML (API-backed).")
    ap.add_argument("-d", "--dir", default=str(DATA_DIR),
                    help="folder holding ln.series and the ln.* mapping files")
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="dimensions to leave out of the picker "
                         "(e.g. --exclude indy occupation)")
    ap.add_argument("-o", "--out", default=None,
                    help="output HTML path (default v2/output/ln_explorer.html)")
    ap.add_argument("--chunk", type=int, default=250,
                    help="series per fetch call; smaller = finer resume "
                         "granularity (default 250)")
    ap.add_argument("--refresh", action="store_true",
                    help="ignore cached series and refetch (costs full quota)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report the catalog and query cost, then stop")
    args = ap.parse_args()

    folder = Path(args.dir).expanduser()
    out_path = bls_client.resolve_out(args.out, "ln_explorer.html")

    print("Building catalog from ln.series ...")
    cat = build_catalog(folder, args.exclude)
    wanted = cat["wanted"]
    print(f"Picker dimensions: {len(cat['dims'])} | value groups: "
          f"{len(cat['combos'])} | series to embed: {len(wanted)} | "
          f"duplicate candidates resolved deterministically: {cat['dupes']}")

    cached = sum(1 for sid in wanted if bls_client.is_cached(sid))
    todo = len(wanted) - cached
    est = estimate_queries(todo, dt.date.today().year)
    print(f"Cache: {cached} of {len(wanted)} series present | "
          f"to fetch: {todo} | estimated queries: ~{est} of 500/day")

    if args.dry_run:
        print("\n--dry-run: stopping before any API call.")
        return

    print("\nFetching observations through the BLS API ...")
    data = fetch_observations(wanted, args.chunk, args.refresh)
    packed = pack(data, wanted)
    print(f"Packed {len(packed)} series "
          f"({sum(len(s['v']) for s in packed.values()):,} monthly slots)")

    n_missing = prune(cat, packed)
    if n_missing:
        print(f"WARNING: pruned {n_missing} combo entries with no data rows")

    payload = {"dims": cat["dims"], "combos": cat["combos"], "series": packed,
               "measures": cat["measures"], "measureOrder": cat["measureOrder"],
               "fixedDefaults": cat["fixedDefaults"],
               "sexLabels": cat["sexLabels"]}
    blob = json.dumps(payload, separators=(",", ":"))
    if not TEMPLATE.is_file():
        sys.exit(f"ERROR: missing template {TEMPLATE}")
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", blob)
    out_path.write_text(html, encoding="utf-8")
    print(f"\nWrote {out_path}  ({out_path.stat().st_size / 1e6:.1f} MB)")
    print(f"API queries this run: {bls_client.queries_made()}")
    print("Open it in a browser; embed as-is in Prismic.")


if __name__ == "__main__":
    main()

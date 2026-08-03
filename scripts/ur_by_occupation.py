#!/usr/bin/env python3
"""
ur_by_occupation.py -- Unemployment rate by occupation, straight from the
BLS LN (CPS) flat files.

What it does, end to end:
  1. Reads ln.series and auto-detects the "clean" unemployment-rate-by-
     occupation series: lfst = unemployment rate, occupation varies, every
     other demographic dimension (sex, age, race, nativity, etc.) held at
     its catalog default. No hardcoded series IDs -- it derives the list,
     so it also prints the list for you to sanity-check.
  2. Streams the big ln.data.* file in chunks and keeps only those series.
  3. Builds a tidy monthly dataset, computes a 12-month moving average
     (these series are mostly NSA, so 12MMA is the honest trend line) and
     year-over-year change.
  4. Prints a ranked latest-month summary, writes a tidy CSV, and saves a
     small-multiples PNG chart.

USAGE:
  python scripts/ur_by_occupation.py
  python scripts/ur_by_occupation.py --start-year 2015 --out ~/Desktop/ur_occ

Requires: pandas, matplotlib   (pip install pandas matplotlib)
Folder must contain: ln.series, ln.lfst, ln.occupation (and ideally the
other small ln.* mapping files), plus ln.data.1.AllData.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# --- Repo layout -------------------------------------------------------------
# <repo>/scripts/<this file>, <repo>/data (BLS flat files), <repo>/output
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
OUT_DIR = REPO_ROOT / "output"


SKIP_FILES = {"ln.series", "ln.txt", "ln.contacts", "ln.footnote"}


def base_name(path: Path) -> str:
    """Filename with any trailing '.txt' stripped (browsers add it)."""
    n = path.name
    return n[:-4] if n.lower().endswith(".txt") else n


def find_file(folder: Path, name: str):
    """Locate a BLS file whether saved as 'ln.series' or 'ln.series.txt'."""
    for cand in (name, name + ".txt", name + ".TXT"):
        p = folder / cand
        if p.exists():
            return p
    return None

# D4TP palette
TEAL, CORAL, PAPER, GOLD = "#085041", "#712B13", "#FBFAF7", "#B8860B"


def read_bls(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False,
                     na_values=[], engine="python")
    df.columns = [c.strip() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    return df


def load_lookups(folder: Path) -> dict:
    """Auto-discover code->label mapping files (same logic as explore_ln)."""
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
        code_cols = [c for c in t.columns if c.endswith("_code")]
        text_cols = [c for c in t.columns if c.endswith("_text")]
        if len(code_cols) == 1 and text_cols:
            lookups[code_cols[0]] = dict(zip(t[code_cols[0]], t[text_cols[0]]))
    return lookups


def match_lookup(lookups: dict, dim_col: str) -> dict:
    """Find the lookup for a series column, tolerating naming drift
    (e.g. series column 'occ_code' vs mapping column 'occupation_code')."""
    if dim_col in lookups:
        return lookups[dim_col]
    pre = dim_col.replace("_code", "")
    for k, v in lookups.items():
        kpre = k.replace("_code", "")
        if kpre.startswith(pre) or pre.startswith(kpre):
            return v
    return {}


def select_series(folder: Path, verbose=True):
    series_path = find_file(folder, "ln.series")
    if series_path is None:
        sys.exit(f"ERROR: could not find ln.series (or ln.series.txt) "
                 f"in {folder}")
    series = read_bls(series_path)
    if "seasonal" not in series.columns:
        series["seasonal"] = series["series_id"].str[2]
    lookups = load_lookups(folder)

    dims = [c for c in series.columns
            if c.endswith("_code") and c != "footnote_codes"]

    # Resolve key dimensions by prefix so column-name drift doesn't bite
    def find_dim(prefix):
        hits = [d for d in dims if d.startswith(prefix)]
        if not hits:
            sys.exit(f"ERROR: no dimension starting with '{prefix}' in "
                     f"ln.series -- columns found: {dims}")
        return hits[0]

    occ_dim = find_dim("occ")
    lfst_dim = find_dim("lfst")
    per_dim = find_dim("periodicity")

    # lfst codes whose label is exactly 'unemployment rate'
    lfst_lk = match_lookup(lookups, lfst_dim)
    ur_codes = [c for c, t in lfst_lk.items()
                if t.strip().lower() == "unemployment rate"]
    if not ur_codes:  # fall back to substring
        ur_codes = [c for c, t in lfst_lk.items()
                    if "unemployment rate" in t.strip().lower()]
    if not ur_codes:
        sys.exit("ERROR: could not find an 'unemployment rate' code in "
                 "ln.lfst -- is that mapping file in the folder?")

    # Catalog default for each dimension = its most common code.
    # (Defaults like 'both sexes' / 'all races' dominate the catalog.)
    defaults = {d: series[d].mode().iloc[0] for d in dims}

    mask = (series[lfst_dim].isin(ur_codes)
            & (series[occ_dim] != defaults[occ_dim])
            & (series[per_dim] == "M"))
    for d in dims:
        if d in (occ_dim, lfst_dim, per_dim):
            continue
        mask &= series[d] == defaults[d]
    sel = series[mask].copy()

    # Keep only currently published series
    end_years = pd.to_numeric(sel["end_year"], errors="coerce")
    sel = sel[end_years == end_years.max()]

    occ_lk = match_lookup(lookups, occ_dim)
    sel["occupation"] = sel[occ_dim].map(occ_lk).fillna(sel[occ_dim])

    if verbose:
        print(f"\nSelected {len(sel)} unemployment-rate-by-occupation series "
              f"(all other demographics at defaults, monthly, active):\n")
        cols = ["series_id", "seasonal", "begin_year", "end_year",
                "occupation"]
        print(sel[cols].sort_values("occupation").to_string(index=False))
        sa = (sel["seasonal"] == "S").sum()
        print(f"\nSeasonal adjustment: {sa} SA / {len(sel) - sa} NSA. "
              f"NSA series get a 12-month moving average below.")
    return sel


def load_data(folder: Path, series_ids: set, data_file=None) -> pd.DataFrame:
    if data_file:
        paths = [Path(data_file)]
    else:
        paths = sorted(folder.glob("ln.data*"))  # matches .txt suffix too
    if not paths:
        sys.exit(f"ERROR: no ln.data.* file found in {folder}. Download "
                 f"ln.data.1.AllData from the BLS LN directory.")
    keep = []
    for p in paths:
        print(f"\nStreaming {p.name} ...")
        for chunk in pd.read_csv(p, sep="\t", dtype=str, chunksize=1_000_000,
                                 keep_default_na=False, na_values=[]):
            chunk.columns = [c.strip() for c in chunk.columns]
            chunk["series_id"] = chunk["series_id"].str.strip()
            hit = chunk[chunk["series_id"].isin(series_ids)]
            if len(hit):
                keep.append(hit)
    if not keep:
        sys.exit("ERROR: none of the selected series IDs were found in the "
                 "data file(s).")
    df = pd.concat(keep, ignore_index=True)
    df = df[df["period"].str.strip().between("M01", "M12")]  # drop M13 annual
    df["value"] = pd.to_numeric(df["value"].str.strip(), errors="coerce")
    df["date"] = pd.to_datetime(df["year"].str.strip() + "-"
                                + df["period"].str.strip().str[1:] + "-01")
    return df[["series_id", "date", "value"]].dropna()


def shorten(label: str, n=38) -> str:
    label = label.replace(" occupations", "").replace(", and ", " & ")
    return label if len(label) <= n else label[:n - 1] + "\u2026"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("-d", "--dir", default=str(DATA_DIR),
                    help="folder with ln.series, mappings, and ln.data.*")
    ap.add_argument("--data", help="explicit path to the data file "
                                   "(default: auto-detect ln.data.* in -d)")
    ap.add_argument("--start-year", type=int, default=2015,
                    help="chart start year (default 2015)")
    ap.add_argument("--out", default=None,
                    help="output folder (default: <dir>/ur_occ_output)")
    args = ap.parse_args()

    folder = Path(args.dir).expanduser()
    out = Path(args.out).expanduser() if args.out else OUT_DIR / "ur_occ_output"
    out.mkdir(parents=True, exist_ok=True)

    sel = select_series(folder)
    data = load_data(folder, set(sel["series_id"]), args.data)

    tidy = data.merge(sel[["series_id", "occupation", "seasonal"]],
                      on="series_id")
    tidy = tidy.sort_values(["occupation", "date"])
    tidy["ur_12mma"] = (tidy.groupby("series_id")["value"]
                        .transform(lambda s: s.rolling(12).mean()))
    tidy["yoy_change"] = tidy.groupby("series_id")["value"].diff(12)

    csv_path = out / "unemployment_rate_by_occupation.csv"
    tidy.to_csv(csv_path, index=False)

    # ---- latest-month summary ----
    latest_date = tidy["date"].max()
    latest = (tidy[tidy["date"] == latest_date]
              .sort_values("value", ascending=False))
    print(f"\n=== Unemployment rate by occupation, "
          f"{latest_date:%B %Y} (ranked) ===\n")
    summary = latest[["occupation", "seasonal", "value", "ur_12mma",
                      "yoy_change"]].rename(columns={
                          "value": "ur_latest",
                          "ur_12mma": "12mo_avg",
                          "yoy_change": "chg_vs_yr_ago"})
    with pd.option_context("display.float_format", "{:.1f}".format,
                           "display.max_colwidth", 70, "display.width", 200):
        print(summary.to_string(index=False))

    # ---- small-multiples chart ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plot = tidy[tidy["date"] >= pd.Timestamp(args.start_year, 1, 1)]
    occs = (latest.sort_values("value", ascending=False)["occupation"]
            .tolist())
    ncols = 3
    nrows = -(-len(occs) // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(13, 3.1 * nrows),
                             sharex=True, sharey=True)
    fig.patch.set_facecolor(PAPER)
    ymax = plot["value"].quantile(0.995) * 1.1

    for ax, occ in zip(axes.flat, occs):
        g = plot[plot["occupation"] == occ]
        ax.set_facecolor(PAPER)
        ax.plot(g["date"], g["value"], color=TEAL, alpha=0.30, lw=1.0)
        ax.plot(g["date"], g["ur_12mma"], color=TEAL, lw=2.2)
        last = g.dropna(subset=["ur_12mma"]).iloc[-1:]
        if len(last):
            ax.scatter(last["date"], last["ur_12mma"], color=CORAL,
                       zorder=5, s=28)
            ax.annotate(f"{last['ur_12mma'].iloc[0]:.1f}%",
                        (last["date"].iloc[0], last["ur_12mma"].iloc[0]),
                        xytext=(6, 4), textcoords="offset points",
                        color=CORAL, fontsize=9, fontweight="bold")
        ax.set_title(shorten(occ), fontsize=10, color=TEAL, loc="left")
        ax.set_ylim(0, ymax)
        ax.grid(axis="y", alpha=0.25)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
    for ax in axes.flat[len(occs):]:
        ax.set_visible(False)

    fig.suptitle("Unemployment rate by occupation "
                 "(monthly NSA, thin; 12-month average, bold)",
                 fontsize=14, color=TEAL, fontweight="bold", x=0.01,
                 ha="left")
    fig.text(0.01, 0.005,
             "Source: BLS Current Population Survey (LN database), "
             f"through {latest_date:%B %Y}. Chart: Data 4 The People.",
             fontsize=8, color=GOLD)
    fig.tight_layout(rect=[0, 0.02, 1, 0.96])
    png_path = out / "ur_by_occupation.png"
    fig.savefig(png_path, dpi=200, facecolor=PAPER)

    print(f"\nWrote:\n  {csv_path}\n  {png_path}")


if __name__ == "__main__":
    main()

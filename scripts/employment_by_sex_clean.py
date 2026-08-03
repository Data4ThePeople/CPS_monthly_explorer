#!/usr/bin/env python3
"""
employment_by_sex_clean.py

The defensible version. NO population-control arithmetic. Instead of trying
to subtract the Jan-2026 break out (which double-counts, as we found), this
segments the window AT the break and never sums across it:

  SEGMENT 1  Dec-2023 -> Dec-2025   (entirely PRE-break: clean, no adjustment)
             Reported NSA Dec-to-Dec so seasonality nets out, and SA for check.
  SEGMENT 2  Dec-2025 -> latest     (POST-break, new population base)
             Current readout only. NOT added to Segment 1.

Why this is honest: the Jan-2026 population control creates a one-time step
between Dec-2025 and Jan-2026. Any window that straddles it carries that step.
By splitting exactly at the seam, each segment sits on a single population
basis, so no subtraction is needed and no sign traps arise. The BLS
population-control table is cited in the PROSE to explain the seam, but it
never enters the math here.

Run from anywhere (data defaults to <repo>/data):
    python3 scripts/employment_by_sex_clean.py

Requires: pandas
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd

# --- Repo layout -------------------------------------------------------------
# <repo>/scripts/<this file>, <repo>/data (BLS flat files), <repo>/output
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
OUT_DIR = REPO_ROOT / "output"


SA = {
    "LNS12000000": "Both sexes",
    "LNS12000001": "Men",
    "LNS12000002": "Women",
}
NSA = {
    "LNU02000000": "Both sexes",
    "LNU02000001": "Men",
    "LNU02000002": "Women",
}
ALL = {**SA, **NSA}

SEG1_START = "2023-12"
SEAM       = "2025-12"   # last pre-break month; Jan-2026 is the break


def load_data(folder, series_ids, data_file):
    paths = [Path(data_file)] if data_file else sorted(folder.glob("ln.data*"))
    if not paths:
        sys.exit(f"ERROR: no ln.data.* file found in {folder}.")
    keep = []
    for p in paths:
        print(f"Streaming {p.name} ...")
        for chunk in pd.read_csv(p, sep="\t", dtype=str, chunksize=1_000_000,
                                 keep_default_na=False, na_values=[]):
            chunk.columns = [c.strip() for c in chunk.columns]
            chunk["series_id"] = chunk["series_id"].str.strip()
            hit = chunk[chunk["series_id"].isin(series_ids)]
            if len(hit):
                keep.append(hit)
    if not keep:
        sys.exit("ERROR: none of the selected series IDs were found.")
    df = pd.concat(keep, ignore_index=True)
    df = df[df["period"].str.strip().between("M01", "M12")]
    df["value"] = pd.to_numeric(df["value"].str.strip(), errors="coerce")
    df["date"] = pd.to_datetime(df["year"].str.strip() + "-"
                                + df["period"].str.strip().str[1:] + "-01")
    return df[["series_id", "date", "value"]].dropna()


def wide(df, mapping):
    d = df[df["series_id"].isin(mapping)].copy()
    d["label"] = d["series_id"].map(mapping)
    return d.pivot_table(index="date", columns="label", values="value").sort_index()


def segment(w, start, end, title):
    print(f"\n{'-'*60}\n{title}\n  {start:%Y-%m} -> {end:%Y-%m}\n{'-'*60}")
    if start not in w.index or end not in w.index:
        print("  endpoint missing on this basis.")
        return None
    ch = {c: w.loc[end, c] - w.loc[start, c] for c in ["Both sexes", "Men", "Women"]}
    for c in ["Both sexes", "Men", "Women"]:
        print(f"    {c:12s}: {ch[c]:>+8,.0f}k")
    if ch["Both sexes"] != 0:
        print(f"    women share of net growth: {ch['Women']/ch['Both sexes']*100:5.1f}%")
        print(f"    men   share of net growth: {ch['Men']/ch['Both sexes']*100:5.1f}%")
    return ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--dir", default=str(DATA_DIR))
    ap.add_argument("--data")
    ap.add_argument("-o", "--out", default=str(OUT_DIR / "employment_by_sex_clean.csv"))
    args = ap.parse_args()

    folder = Path(args.dir).expanduser()
    seg1_start = pd.to_datetime(SEG1_START + "-01")
    seam = pd.to_datetime(SEAM + "-01")

    df = load_data(folder, set(ALL), args.data)
    sa = wide(df, SA)
    nsa = wide(df, NSA)
    latest = df["date"].max()

    print("\n" + "#" * 60)
    print("# CLEAN SEGMENTED VIEW - no population-control arithmetic")
    print("# Each segment sits on ONE population basis. Never sum across")
    print("# the Jan-2026 seam.")
    print("#" * 60)

    print("\n" + "=" * 60)
    print("SEGMENT 1  (PRE-BREAK, CLEAN - this is your headline window)")
    print("=" * 60)
    s1_nsa = segment(nsa, seg1_start, seam, "NSA, Dec-to-Dec (seasonality nets out) [PRIMARY]")
    s1_sa  = segment(sa,  seg1_start, seam, "SA (robustness check)")

    print("\n" + "=" * 60)
    print("SEGMENT 2  (POST-BREAK, current readout - report SEPARATELY)")
    print("=" * 60)
    segment(nsa, seam, latest, "NSA, Dec-2025 -> latest")
    segment(sa,  seam, latest, "SA, Dec-2025 -> latest")

    # tidy export, both bases, full window for charting
    out = pd.concat([sa.add_suffix(" (SA)"), nsa.add_suffix(" (NSA)")], axis=1)
    out = out[out.index >= seg1_start].sort_index()
    out.index.name = "date"
    out_path = folder / args.out
    out.to_csv(out_path, float_format="%.0f")
    print(f"\nWrote: {out_path}")

    print("\n" + "=" * 60)
    print("HOW TO STATE IT:")
    if s1_nsa and s1_nsa["Both sexes"] != 0:
        ws = s1_nsa["Women"] / s1_nsa["Both sexes"] * 100
        print(f"  Over the clean pre-break window (Dec-2023 to Dec-2025), women")
        print(f"  were {ws:.0f}% of net employment growth (NSA Dec-to-Dec).")
    print("  The Jan-2026 population controls create a break; we report the")
    print("  months after it separately and do not sum across it. Cite BLS")
    print("  empsit_03062026 Table A/B in prose as the reason for the seam.")
    print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
pull_employment_by_sex.py

Pulls CPS (LN) seasonally adjusted employment-level series for Both / Men / Women,
16+, from the local BLS flat file and computes the growth since a baseline month
(default: December 2023). Writes a tidy CSV you can drop straight into a chart,
plus a short console summary of the men-vs-women split.

Run from ~/Desktop/ln/  (or point --dir at it):
    python3 pull_employment_by_sex.py

Requires: pandas  (pip install --user pandas  if needed)
BLS flat file expected: ln.data.1.AllData.txt  (tab-separated; auto-detected)
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd

# ---- CPS seasonally adjusted employment level, 16+ -------------------------
# LNS = seasonally adjusted; final digit 0=Both, 1=Men, 2=Women
SERIES = {
    "LNS12000000": "Both sexes",
    "LNS12000001": "Men",
    "LNS12000002": "Women",
}
# Not-seasonally-adjusted equivalents, in case you want to swap:
#   LNU02000000 Both, LNU02000001 Men, LNU02000002 Women  (use --nsa)
NSA_SERIES = {
    "LNU02000000": "Both sexes",
    "LNU02000001": "Men",
    "LNU02000002": "Women",
}


def load_data(folder: Path, series_ids: set, data_file: str | None) -> pd.DataFrame:
    if data_file:
        paths = [Path(data_file)]
    else:
        paths = sorted(folder.glob("ln.data*"))
    if not paths:
        sys.exit(f"ERROR: no ln.data.* file found in {folder}. "
                 f"Download ln.data.1.AllData from the BLS LN directory.")
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
        sys.exit("ERROR: none of the selected series IDs were found in the data file.")
    df = pd.concat(keep, ignore_index=True)
    df = df[df["period"].str.strip().between("M01", "M12")]  # drop M13 annual avg
    df["value"] = pd.to_numeric(df["value"].str.strip(), errors="coerce")
    df["date"] = pd.to_datetime(df["year"].str.strip() + "-"
                                + df["period"].str.strip().str[1:] + "-01")
    return df[["series_id", "date", "value"]].dropna()


def main():
    ap = argparse.ArgumentParser(description="CPS employment growth by sex since a baseline month.")
    ap.add_argument("-d", "--dir", default=".", help="folder with ln.data.* (default: current dir)")
    ap.add_argument("--data", help="explicit path to the data file (default: auto-detect ln.data.*)")
    ap.add_argument("--baseline", default="2023-12", help="baseline month YYYY-MM (default 2023-12)")
    ap.add_argument("--nsa", action="store_true", help="use not-seasonally-adjusted series instead of SA")
    ap.add_argument("-o", "--out", default="employment_by_sex.csv", help="output CSV path")
    args = ap.parse_args()

    folder = Path(args.dir).expanduser()
    series = NSA_SERIES if args.nsa else SERIES
    baseline = pd.to_datetime(args.baseline + "-01")

    df = load_data(folder, set(series), args.data)
    df["label"] = df["series_id"].map(series)

    # Wide: one column per label, indexed by date
    wide = df.pivot_table(index="date", columns="label", values="value").sort_index()
    wide = wide[wide.index >= baseline]

    if baseline not in wide.index:
        sys.exit(f"ERROR: baseline month {args.baseline} not present in the data.")

    base = wide.loc[baseline]

    # Change vs baseline (in thousands, the native unit)
    change = wide.subtract(base, axis=1)
    change.columns = [f"{c} — change since {args.baseline} (000s)" for c in change.columns]

    out = pd.concat([wide, change], axis=1)
    out.index.name = "date"
    out_path = folder / args.out
    out.to_csv(out_path, float_format="%.0f")
    print(f"\nWrote: {out_path}")

    # ---- Console summary ---------------------------------------------------
    latest = wide.index.max()
    d_men = wide.loc[latest, "Men"] - base["Men"]
    d_women = wide.loc[latest, "Women"] - base["Women"]
    d_both = wide.loc[latest, "Both sexes"] - base["Both sexes"]

    print("\n" + "=" * 60)
    print(f"CPS employment change: {args.baseline}  ->  {latest:%Y-%m}")
    print(f"({'NSA' if args.nsa else 'SA'}, 16+, level in thousands)")
    print("=" * 60)
    print(f"  Both sexes:  {d_both:>+9,.0f}k")
    print(f"  Men:         {d_men:>+9,.0f}k")
    print(f"  Women:       {d_women:>+9,.0f}k")
    if d_both != 0:
        print(f"\n  Women share of net growth: {d_women / d_both * 100:5.1f}%")
        print(f"  Men   share of net growth: {d_men   / d_both * 100:5.1f}%")
    print("=" * 60)
    print("\nCSV columns: monthly levels + change-since-baseline for each of")
    print("Both / Men / Women. Feed the change columns straight into a chart.")


if __name__ == "__main__":
    main()

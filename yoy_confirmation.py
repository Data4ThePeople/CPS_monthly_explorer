#!/usr/bin/env python3
"""
yoy_confirmation.py

The currency check: June-2025 -> June-2026 over-the-year change in employed
persons by sex, with the published BLS population-control effect subtracted
per BLS's own Table B procedure.

WHY THIS WINDOW IS THE ONE PLACE THE SUBTRACTION IS VALID:
  - Matched months (Jun -> Jun) cancel seasonality exactly. No seasonal
    factors are involved, so we run on the NSA series, which is also the
    basis the published effect is measured on. Basis-consistent throughout.
  - The window straddles the Jan-2026 break exactly once, the configuration
    BLS's method is designed for: "the effect of the 2026 population control
    would be subtracted from the over-the-year change to remove the effects
    of the population control adjustment." (BLS empsit_03062026, Table B note)

Published effect on the EMPLOYED level (thousands, NSA, Dec-2025 basis),
BLS Employment Situation release, March 6 2026, Table A:
    Both = -1,432    Men = -1,588    Women = +155

Run from ~/Desktop/ln/:
    python3 yoy_confirmation.py
Optionally check another matched pair:
    python3 yoy_confirmation.py --month 2026-05   (compares vs 2025-05)

Requires: pandas
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd

NSA = {
    "LNU02000000": "Both sexes",
    "LNU02000001": "Men",
    "LNU02000002": "Women",
}

POP_CTL_EFFECT = {   # thousands; positive = adjustment raised the level
    "Both sexes": -1432,
    "Men":        -1588,
    "Women":       155,
}


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--dir", default=".")
    ap.add_argument("--data")
    ap.add_argument("--month", default="2026-06",
                    help="end month YYYY-MM; compares against same month prior year")
    args = ap.parse_args()

    folder = Path(args.dir).expanduser()
    end = pd.to_datetime(args.month + "-01")
    start = end - pd.DateOffset(years=1)

    df = load_data(folder, set(NSA), args.data)
    d = df.copy()
    d["label"] = d["series_id"].map(NSA)
    w = d.pivot_table(index="date", columns="label", values="value").sort_index()

    for dt, tag in [(start, "start"), (end, "end")]:
        if dt not in w.index:
            sys.exit(f"ERROR: {tag} month {dt:%Y-%m} not in data.")

    # sanity: window must straddle the Jan-2026 break exactly once
    brk = pd.to_datetime("2026-01-01")
    straddles = start < brk <= end
    print("\n" + "#" * 62)
    print(f"# YoY window: {start:%Y-%m} -> {end:%Y-%m}  (NSA, matched months)")
    if straddles:
        print("# Window straddles the Jan-2026 break once -> BLS Table B")
        print("# subtraction applies. Adjusted figures below are valid.")
    else:
        print("# WARNING: window does NOT straddle the Jan-2026 break.")
        print("# Do NOT use the adjusted column; raw is already clean.")
    print("#" * 62)

    print(f"\n  {'':12s}{'RAW YoY':>12s}{'pop-ctl effect':>16s}{'ADJUSTED YoY':>14s}")
    raw, adj = {}, {}
    for c in ["Both sexes", "Men", "Women"]:
        raw[c] = w.loc[end, c] - w.loc[start, c]
        adj[c] = raw[c] - POP_CTL_EFFECT[c] if straddles else raw[c]
        eff = POP_CTL_EFFECT[c] if straddles else 0
        print(f"  {c:12s}{raw[c]:>+11,.0f}k{eff:>+15,.0f}k{adj[c]:>+13,.0f}k")

    use = adj if straddles else raw
    label = "ADJUSTED" if straddles else "RAW"
    if use["Both sexes"] != 0:
        print(f"\n  {label} women share of net YoY change: "
              f"{use['Women']/use['Both sexes']*100:5.1f}%")
        print(f"  {label} men   share of net YoY change: "
              f"{use['Men']/use['Both sexes']*100:5.1f}%")
    else:
        print("\n  Net change is zero; shares undefined.")

    print("\n" + "=" * 62)
    print("READ: if the adjusted YoY women's share lands near the ~60% from")
    print("the clean Dec-2023 -> Dec-2025 window, the headline is confirmed")
    print("and current. If it diverges, the 2026 composition shifted; report")
    print("that as a development, not a contradiction. Note small-sample")
    print("caution: CPS monthly changes carry wide confidence intervals, so")
    print("treat a few points of share difference as noise, not signal.")
    print("=" * 62)


if __name__ == "__main__":
    main()

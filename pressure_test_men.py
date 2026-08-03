#!/usr/bin/env python3
"""
pressure_test_men.py

Pressure-tests the "men's employment fell 811k since Dec 2023" finding by
showing the MONTHLY path, not just the endpoints. Flags:
  - the single largest month-over-month moves for Men (where did the drop happen?)
  - the Jan-2026 step specifically (the population-control re-benchmark month,
    footnote 12) for Both / Men / Women, so you can see if the drop is a
    behavioral trend or a one-month benchmark artifact.
  - a NSA cross-check of the same endpoints, so seasonal adjustment isn't
    doing the work.

Run from ~/Desktop/ln/:
    python3 pressure_test_men.py

Requires: pandas
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd

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
ALL_SERIES = {**SA, **NSA}


def load_data(folder: Path, series_ids: set, data_file: str | None) -> pd.DataFrame:
    if data_file:
        paths = [Path(data_file)]
    else:
        paths = sorted(folder.glob("ln.data*"))
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


def sa_wide(df, mapping, baseline):
    d = df[df["series_id"].isin(mapping)].copy()
    d["label"] = d["series_id"].map(mapping)
    w = d.pivot_table(index="date", columns="label", values="value").sort_index()
    return w[w.index >= baseline]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--dir", default=".")
    ap.add_argument("--data")
    ap.add_argument("--baseline", default="2023-12")
    ap.add_argument("-o", "--out", default="men_monthly_path.csv")
    args = ap.parse_args()

    folder = Path(args.dir).expanduser()
    baseline = pd.to_datetime(args.baseline + "-01")

    df = load_data(folder, set(ALL_SERIES), args.data)
    sa = sa_wide(df, SA, baseline)
    nsa = sa_wide(df, NSA, baseline)

    # --- Monthly changes for Men (SA) --------------------------------------
    men = sa["Men"]
    mom = men.diff()  # month-over-month change, thousands

    # Save full monthly path with MoM deltas
    out = sa.copy()
    out["Men MoM (000s)"] = mom
    out["Women MoM (000s)"] = sa["Women"].diff()
    out["Both MoM (000s)"] = sa["Both sexes"].diff()
    out.index.name = "date"
    out_path = folder / args.out
    out.to_csv(out_path, float_format="%.0f")
    print(f"\nWrote: {out_path}")

    latest = sa.index.max()
    total_men = men.loc[latest] - men.loc[baseline]

    # --- 1) Where did the men's drop happen? -------------------------------
    print("\n" + "=" * 64)
    print(f"1) MEN, largest month-over-month moves (SA), {args.baseline}->{latest:%Y-%m}")
    print("=" * 64)
    print(f"  Total men change over window: {total_men:>+8,.0f}k")
    ranked = mom.dropna().sort_values()
    print("\n  Biggest single-month DROPS:")
    for dt, v in ranked.head(6).items():
        flag = "  <-- Jan-2026 rebenchmark" if (dt.year == 2026 and dt.month == 1) else ""
        print(f"    {dt:%Y-%m}: {v:>+7,.0f}k{flag}")
    print("\n  Biggest single-month GAINS:")
    for dt, v in ranked.tail(4).items():
        print(f"    {dt:%Y-%m}: {v:>+7,.0f}k")

    # How concentrated is the drop? share of total decline from worst month
    worst_dt = ranked.index[0]
    worst_v = ranked.iloc[0]
    if total_men < 0:
        print(f"\n  Worst month ({worst_dt:%Y-%m}) = {worst_v:+,.0f}k, "
              f"{worst_v/total_men*100:.0f}% of the net men decline.")

    # --- 2) The Jan-2026 step specifically ---------------------------------
    jan = pd.to_datetime("2026-01-01")
    print("\n" + "=" * 64)
    print("2) JAN-2026 re-benchmark month, MoM step (SA)")
    print("=" * 64)
    if jan in sa.index and (jan - pd.DateOffset(months=1)) in sa.index:
        for c in ["Both sexes", "Men", "Women"]:
            step = sa.loc[jan, c] - sa.loc[jan - pd.DateOffset(months=1), c]
            print(f"    {c:12s}: {step:>+7,.0f}k  (Dec-2025 -> Jan-2026)")
        print("\n  Note: SA employment levels absorb new population controls in")
        print("  January. A large one-month step here is partly mechanical, not")
        print("  purely behavioral. Tie this out the way you did the race piece.")
    else:
        print("  Jan-2026 or Dec-2025 not in range.")

    # --- 3) NSA endpoint cross-check ---------------------------------------
    print("\n" + "=" * 64)
    print("3) NSA endpoint cross-check (is SA doing the work?)")
    print("=" * 64)
    if baseline in nsa.index and latest in nsa.index:
        for c in ["Both sexes", "Men", "Women"]:
            d = nsa.loc[latest, c] - nsa.loc[baseline, c]
            print(f"    {c:12s}: {d:>+8,.0f}k  (NSA, {args.baseline}->{latest:%Y-%m})")
        print("\n  Compare signs/magnitudes to the SA result. NSA endpoints")
        print("  Dec->Jun mix in seasonality, so they won't match exactly, but")
        print("  the men-down / women-up direction should survive.")
    else:
        print("  NSA baseline or latest month not in range.")
    print("=" * 64)


if __name__ == "__main__":
    main()

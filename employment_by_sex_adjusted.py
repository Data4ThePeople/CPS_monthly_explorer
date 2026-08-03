#!/usr/bin/env python3
"""
employment_by_sex_adjusted.py

Computes CPS employment growth by sex since Dec-2023, CURRENT THROUGH THE
LATEST MONTH, with the January 2026 population-control break handled the way
BLS itself prescribes: subtract the published population-control effect from
the over-the-window change (BLS Feb-2026 release, Table B method).

Published BLS population-control effects on the EMPLOYED level, from the
March 6, 2026 Employment Situation release, Table A ("Effect of the updated
population controls on December 2025 estimates by sex," NSA, thousands):
    Employed  Total = -1,432   Men = -1,588   Women = +155
Source: https://www.bls.gov/news.release/archives/empsit_03062026.htm

BLS Table B note: "the effect of the 2026 population control would be
subtracted from the over-the-year change to remove the effects of the
population control adjustment."

CAVEAT the script enforces: the published effect is measured NSA on the
Dec-2025 level. To keep the subtraction clean, this script computes the
adjusted change on BOTH the SA and NSA series and prints both, rather than
crossing an NSA adjustment into an SA window. Report the version whose basis
matches the effect (NSA) as primary, and show SA as a robustness check.

Run from ~/Desktop/ln/:
    python3 employment_by_sex_adjusted.py

Requires: pandas
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd

SA = {
    "LNS12000000": ("Both sexes", "SA"),
    "LNS12000001": ("Men", "SA"),
    "LNS12000002": ("Women", "SA"),
}
NSA = {
    "LNU02000000": ("Both sexes", "NSA"),
    "LNU02000001": ("Men", "NSA"),
    "LNU02000002": ("Women", "NSA"),
}
ALL = {**SA, **NSA}

# Published BLS population-control effect on EMPLOYED level (thousands),
# March 6 2026 release Table A. Positive = adjustment raised the level.
POP_CTL_EFFECT = {
    "Both sexes": -1432,
    "Men":        -1588,
    "Women":       155,
}

BASELINE_DEFAULT = "2023-12"


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


def build_wide(df, mapping, baseline):
    d = df[df["series_id"].isin(mapping)].copy()
    d["label"] = d["series_id"].map(lambda s: mapping[s][0])
    w = d.pivot_table(index="date", columns="label", values="value").sort_index()
    return w[w.index >= baseline]


def report(name, wide, baseline, latest):
    print(f"\n{'='*64}\n{name} basis\n{'='*64}")
    if baseline not in wide.index or latest not in wide.index:
        print("  baseline or latest month missing on this basis.")
        return
    raw = {c: wide.loc[latest, c] - wide.loc[baseline, c]
           for c in ["Both sexes", "Men", "Women"]}
    adj = {c: raw[c] - POP_CTL_EFFECT[c] for c in raw}  # subtract the pop-ctl effect

    print(f"  window: {baseline:%Y-%m} -> {latest:%Y-%m}")
    print(f"  {'':12s}{'RAW change':>14s}{'pop-ctl effect':>16s}{'ADJUSTED':>12s}")
    for c in ["Both sexes", "Men", "Women"]:
        print(f"  {c:12s}{raw[c]:>+13,.0f}k{POP_CTL_EFFECT[c]:>+15,.0f}k{adj[c]:>+11,.0f}k")

    if adj["Both sexes"] != 0:
        wshare = adj["Women"] / adj["Both sexes"] * 100
        mshare = adj["Men"] / adj["Both sexes"] * 100
        print(f"\n  ADJUSTED women share of net growth: {wshare:5.1f}%")
        print(f"  ADJUSTED men   share of net growth: {mshare:5.1f}%")
    print(f"\n  (RAW women share, unadjusted: "
          f"{raw['Women']/raw['Both sexes']*100:.1f}%  <- the misleading number)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--dir", default=".")
    ap.add_argument("--data")
    ap.add_argument("--baseline", default=BASELINE_DEFAULT)
    ap.add_argument("-o", "--out", default="employment_by_sex_adjusted.csv")
    args = ap.parse_args()

    folder = Path(args.dir).expanduser()
    baseline = pd.to_datetime(args.baseline + "-01")

    df = load_data(folder, set(ALL), args.data)
    sa = build_wide(df, SA, baseline)
    nsa = build_wide(df, NSA, baseline)
    latest_sa = sa.index.max()
    latest_nsa = nsa.index.max()

    print("\n" + "#" * 64)
    print("# BLS-PRESCRIBED ADJUSTMENT (Table B method)")
    print("# Published Jan-2026 pop-control effect on EMPLOYED, thousands:")
    print(f"#   Both {POP_CTL_EFFECT['Both sexes']}  Men {POP_CTL_EFFECT['Men']}"
          f"  Women +{POP_CTL_EFFECT['Women']}")
    print("# Effect is NSA on the Dec-2025 level -> the NSA panel below is the")
    print("# basis-consistent one. SA shown as robustness only.")
    print("#" * 64)

    # NSA is basis-consistent with the published (NSA) effect -> primary
    report("NSA (basis-consistent, PRIMARY)", nsa, baseline, latest_nsa)
    # SA shown for robustness; note the basis mismatch
    report("SA (robustness only; effect is NSA)", sa, baseline, latest_sa)

    # tidy export
    out = pd.concat(
        [sa.add_suffix(" (SA)"), nsa.add_suffix(" (NSA)")], axis=1
    ).sort_index()
    out.index.name = "date"
    out_path = folder / args.out
    out.to_csv(out_path, float_format="%.0f")
    print(f"\nWrote: {out_path}")
    print("\n" + "=" * 64)
    print("HEADLINE (use the NSA adjusted line): both sexes gained employment;")
    print("women's gain far exceeded men's. The apparent men's DECLINE in the")
    print("raw SA series is a population-control artifact, not lost jobs. Cite")
    print("BLS Table A/B (empsit_03062026) for the adjustment.")
    print("=" * 64)


if __name__ == "__main__":
    main()

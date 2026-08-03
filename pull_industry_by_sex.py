#!/usr/bin/env python3
"""
pull_industry_by_sex.py

Tests the care-economy tie the DEFENSIBLE way: entirely inside the CPS
(household survey), never mixing in CES. Pulls CPS employed-by-industry,
split by sex, for the health-related industry groups, and shows:

  - the standing female SHARE of each industry (composition), and
  - the female share of the CHANGE since the baseline (growth decomposition),

reported around the Jan-2026 population-control break, not across it.

IMPORTANT DEFINITIONAL NOTE printed at runtime: the CPS publishes industry at
the MAJOR GROUP level. The nearest group is "Education and health services,"
which is BROADER than the CES "Health care and social assistance" used in the
NFP piece -- it folds in education. This script also attempts to pull finer
health-specific children if they exist in your catalog, and flags any series
ID it cannot find so you know exactly what your file supports.

Run from ~/Desktop/ln/:
    python3 pull_industry_by_sex.py

Requires: pandas
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd

# ---------------------------------------------------------------------------
# CONFIRMED from your prior sum-check reconciliation (NSA, employed level):
#   Education and health services: both / men / women
CONFIRMED = {
    "Education and health services": {
        "both":  "LNU02034574",
        "men":   "LNU02037841",
        "women": "LNU02037935",
    },
}

# CANDIDATE finer children. These are NOT yet confirmed against your catalog.
# The script will report which of these actually resolve in your data file so
# you can trust only the ones that return rows. Do NOT publish off any triple
# that does not first pass the Men+Women=Both check below.
CANDIDATES = {
    # Fill these in from your ln.series / explore_ln.py catalog if present.
    # Leaving them empty by default so the script runs clean on the confirmed
    # group and you add children only after you've looked them up.
    # Example shape:
    # "Health care and social assistance": {
    #     "both": "LNU0203XXXX", "men": "LNU0203YYYY", "women": "LNU0203ZZZZ"},
}

BASELINE_DEFAULT = "2023-12"
BREAK_MONTH = "2026-01"  # population-control re-benchmark, footnote 12


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


def series_at(df, sid, dt):
    sub = df[(df["series_id"] == sid) & (df["date"] == dt)]
    return None if sub.empty else float(sub["value"].iloc[0])


def analyze_group(df, name, ids, baseline, brk, latest):
    both_id, men_id, women_id = ids["both"], ids["men"], ids["women"]
    have = set(df["series_id"].unique())
    missing = [s for s in (both_id, men_id, women_id) if s not in have]
    if missing:
        print(f"\n[SKIP] {name}: series not found in data file: {missing}")
        return None

    def trio(dt):
        return (series_at(df, both_id, dt),
                series_at(df, men_id, dt),
                series_at(df, women_id, dt))

    rows = []
    for tag, dt in [("baseline", baseline), ("break_pre", brk - pd.DateOffset(months=1)),
                    ("break", brk), ("latest", latest)]:
        b, m, w = trio(dt)
        rows.append((tag, dt, b, m, w))

    print(f"\n{'='*66}\n{name}\n{'='*66}")
    print(f"  series: both={both_id} men={men_id} women={women_id}")

    # additivity check at latest
    b, m, w = trio(latest)
    if None not in (b, m, w):
        err = abs((m + w) - b)
        print(f"  additivity (latest): men+women-both = {err:+.0f}k "
              f"({'OK' if err <= 5 else 'CHECK -- exceeds rounding'})")
        print(f"  female SHARE of the industry (latest): {w/b*100:5.1f}%")

    # growth decomposition, split at the break
    b0, m0, w0 = trio(baseline)
    bpre, mpre, wpre = trio(brk - pd.DateOffset(months=1))
    bL, mL, wL = trio(latest)

    if None not in (b0, m0, w0, bpre, mpre, wpre):
        dW_pre = wpre - w0
        dM_pre = mpre - m0
        dB_pre = bpre - b0
        print(f"\n  PRE-BREAK segment ({baseline:%Y-%m} -> {(brk-pd.DateOffset(months=1)):%Y-%m}, clean):")
        print(f"    women change: {dW_pre:>+7,.0f}k")
        print(f"    men   change: {dM_pre:>+7,.0f}k")
        print(f"    both  change: {dB_pre:>+7,.0f}k")
        if dB_pre != 0:
            print(f"    women share of net industry growth: {dW_pre/dB_pre*100:5.1f}%")

    if None not in (bL, mL, wL, b, ):
        dW_post = wL - series_at(df, women_id, brk)
        dM_post = mL - series_at(df, men_id, brk)
        dB_post = bL - series_at(df, both_id, brk)
        print(f"\n  POST-BREAK segment ({brk:%Y-%m} -> {latest:%Y-%m}, new pop base):")
        print(f"    women change: {dW_post:>+7,.0f}k")
        print(f"    men   change: {dM_post:>+7,.0f}k")
        print(f"    both  change: {dB_post:>+7,.0f}k")

    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--dir", default=".")
    ap.add_argument("--data")
    ap.add_argument("--baseline", default=BASELINE_DEFAULT)
    ap.add_argument("-o", "--out", default="industry_by_sex.csv")
    args = ap.parse_args()

    folder = Path(args.dir).expanduser()
    baseline = pd.to_datetime(args.baseline + "-01")
    brk = pd.to_datetime(BREAK_MONTH + "-01")

    groups = {**CONFIRMED, **CANDIDATES}
    all_ids = set()
    for ids in groups.values():
        all_ids.update(ids.values())

    df = load_data(folder, all_ids, args.data)
    latest = df["date"].max()

    print("\n" + "#" * 66)
    print("# DEFINITIONAL NOTE")
    print("# CPS industry is at the MAJOR GROUP level. 'Education and health")
    print("# services' is BROADER than the CES 'Health care and social")
    print("# assistance' from your NFP piece: it includes education. Report")
    print("# these as different measures. Do not equate them in prose.")
    print("#" * 66)

    # Export tidy monthly panel for whichever groups resolve
    resolved_ids = [sid for sid in all_ids if sid in set(df["series_id"].unique())]
    panel = df[df["series_id"].isin(resolved_ids)].pivot_table(
        index="date", columns="series_id", values="value").sort_index()
    panel = panel[panel.index >= baseline]
    out_path = folder / args.out
    panel.to_csv(out_path, float_format="%.0f")
    print(f"\nWrote tidy panel: {out_path}")

    for name, ids in groups.items():
        analyze_group(df, name, ids, baseline, brk, latest)

    print("\n" + "=" * 66)
    print("READ ME: the PRE-BREAK segment is your clean, publishable window.")
    print("It never crosses the Jan-2026 population-control step. If women's")
    print("share of net industry growth there is high, THAT is the demonstrated")
    print("care-economy tie, inside one survey, around the break. The standing")
    print("female SHARE tells you composition; the segment change tells you")
    print("where the marginal jobs went. You need both to earn the claim.")
    print("=" * 66)


if __name__ == "__main__":
    main()

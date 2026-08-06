#!/usr/bin/env python3
"""Pressure-tests the men's-employment finding by showing the MONTHLY path.

Port of scripts/pressure_test_men.py to the BLS API. Flags:
  - the single largest month-over-month moves for Men (where did the drop
    happen?), with the Jan-2026 re-benchmark month labelled,
  - the Jan-2026 step specifically for Both / Men / Women, so you can see if
    the drop is a behavioral trend or a one-month benchmark artifact,
  - an NSA cross-check of the same endpoints, so seasonal adjustment isn't
    doing the work.

Fixes vs the legacy script: a --baseline outside the data exits cleanly with
the available range; the biggest gains print largest first; and the "MoM"
value after the uncollected Oct-2025 (which would actually be a two-month
Sep->Nov change) is masked out rather than ranked as a fake one-month move.

Run from anywhere:
    python v2/pressure_test_men.py [--baseline 2023-12] [-o out.csv] [--refresh]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bls_client
import series_registry as reg

COLS = ["Both sexes", "Men", "Women"]


def masked_mom(series: pd.Series) -> pd.Series:
    """Month-over-month diff with gap-spanning values masked to NaN."""
    mom = series.diff()
    gap = reg.noncontiguous_diff_mask(series.index)
    if gap.any():
        for dt in series.index[gap]:
            print(f"[note] {dt:%Y-%m}: previous calendar month is missing "
                  f"(Oct-2025 was never collected) -- MoM masked, not a real "
                  f"one-month change.")
        mom[gap] = pd.NA
    return mom


def main():
    ap = argparse.ArgumentParser(
        description="Monthly path behind the men's-employment finding "
                    "(SA, with NSA endpoint cross-check).")
    ap.add_argument("--baseline", default=reg.DEFAULT_BASELINE,
                    help=f"window start YYYY-MM (default {reg.DEFAULT_BASELINE})")
    ap.add_argument("-o", "--out",
                    help="output CSV (default <repo>/v2/output/men_monthly_path.csv)")
    bls_client.add_client_args(ap)
    args = ap.parse_args()

    try:
        baseline = pd.to_datetime(args.baseline + "-01")
    except ValueError:
        sys.exit(f"ERROR: --baseline must be YYYY-MM, got {args.baseline!r}")

    ids = list(reg.EMPLOYED_BY_SEX_SA) + list(reg.EMPLOYED_BY_SEX_NSA)
    df = bls_client.fetch(ids, refresh=args.refresh)
    reg.check_break_footnote(df)
    sa = bls_client.to_wide(df, reg.EMPLOYED_BY_SEX_SA)
    nsa = bls_client.to_wide(df, reg.EMPLOYED_BY_SEX_NSA)

    if baseline not in sa.index:
        sys.exit(f"ERROR: baseline {args.baseline} not in the data "
                 f"({sa.index.min():%Y-%m} .. {sa.index.max():%Y-%m}).")
    sa, nsa = sa[sa.index >= baseline], nsa[nsa.index >= baseline]

    men = sa["Men"]
    mom = masked_mom(men)

    # full monthly path with MoM deltas (legacy-compatible columns)
    out = sa.copy()
    out["Men MoM (000s)"] = mom
    out["Women MoM (000s)"] = masked_mom(sa["Women"])
    out["Both MoM (000s)"] = masked_mom(sa["Both sexes"])
    out.index.name = "date"
    out_path = bls_client.resolve_out(args.out, "men_monthly_path.csv")
    out.to_csv(out_path, float_format="%.0f", encoding="utf-8-sig")
    print(f"\nWrote: {out_path}")

    latest = sa.index.max()
    total_men = men.loc[latest] - men.loc[baseline]

    # --- 1) Where did the men's move happen? -------------------------------
    print("\n" + "=" * 64)
    print(f"1) MEN, largest month-over-month moves (SA), "
          f"{args.baseline}->{latest:%Y-%m}")
    print("=" * 64)
    reg.warn_if_crosses_break(baseline, latest, "total window")
    print(f"  Total men change over window: {total_men:>+8,.0f}k")
    ranked = mom.dropna().sort_values()
    print("\n  Biggest single-month DROPS:")
    for dt, v in ranked.head(6).items():
        flag = "  <-- Jan-2026 rebenchmark" if dt == reg.BREAK_MONTH else ""
        print(f"    {dt:%Y-%m}: {v:>+7,.0f}k{flag}")
    print("\n  Biggest single-month GAINS (largest first):")
    for dt, v in ranked.tail(4).sort_values(ascending=False).items():
        print(f"    {dt:%Y-%m}: {v:>+7,.0f}k")

    if len(ranked) and total_men < 0:
        worst_dt, worst_v = ranked.index[0], ranked.iloc[0]
        print(f"\n  Worst month ({worst_dt:%Y-%m}) = {worst_v:+,.0f}k, "
              f"{worst_v / total_men * 100:.0f}% of the net men decline.")

    # --- 2) The Jan-2026 step specifically ---------------------------------
    print("\n" + "=" * 64)
    print("2) JAN-2026 re-benchmark month, MoM step (SA)")
    print("=" * 64)
    if reg.BREAK_MONTH in sa.index and reg.PRE_BREAK_END in sa.index:
        for c in COLS:
            step = sa.loc[reg.BREAK_MONTH, c] - sa.loc[reg.PRE_BREAK_END, c]
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
        for c in COLS:
            d = nsa.loc[latest, c] - nsa.loc[baseline, c]
            print(f"    {c:12s}: {d:>+8,.0f}k  (NSA, {args.baseline}->{latest:%Y-%m})")
        print("\n  Compare signs/magnitudes to the SA result. NSA endpoints")
        print("  Dec->Jun mix in seasonality, so they won't match exactly, but")
        print("  the direction should survive.")
    else:
        print("  NSA baseline or latest month not in range.")
    print("=" * 64)


if __name__ == "__main__":
    main()

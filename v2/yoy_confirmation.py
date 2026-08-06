#!/usr/bin/env python3
"""Matched-month YoY change in employed persons by sex, NSA.

Port of scripts/yoy_confirmation.py to the BLS API. Matched months cancel
seasonality exactly, and the NSA basis is the one the published
population-control effect is measured on -- so a window that straddles the
Jan-2026 break exactly once is the ONE configuration where subtracting the
published effect is valid ("the effect of the 2026 population control would
be subtracted from the over-the-year change", BLS empsit_03062026, Table B
note). Everywhere else in this repo the rule stands: segment, don't subtract.

Fixes vs the legacy script: the end month defaults to the latest available
month (falling back month by month with a note, instead of hard-exiting on a
stale hardcoded date), and the share of net change is suppressed when the
adjusted base is too small to divide by -- a near-zero denominator produced
a meaningless 169% women's share from the legacy defaults.

Run from anywhere:
    python v2/yoy_confirmation.py [--month 2026-06] [--min-base 500] [--refresh]
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


def pick_window(w: pd.DataFrame, month_arg: str | None):
    """Return (start, end) matched months present in the index. With no
    --month, walk back from the latest month until the prior-year match
    exists too."""
    if month_arg:
        try:
            end = pd.to_datetime(month_arg + "-01")
        except ValueError:
            sys.exit(f"ERROR: --month must be YYYY-MM, got {month_arg!r}")
        start = end - pd.DateOffset(years=1)
        for dt, tag in [(start, "start"), (end, "end")]:
            if dt not in w.index:
                sys.exit(f"ERROR: {tag} month {dt:%Y-%m} not in data "
                         f"({w.index.min():%Y-%m} .. {w.index.max():%Y-%m}).")
        return start, end
    end = w.index.max()
    while end >= w.index.min():
        start = end - pd.DateOffset(years=1)
        if end in w.index and start in w.index:
            if end != w.index.max():
                print(f"[note] latest month lacks a prior-year match; "
                      f"using {end:%Y-%m} instead.")
            return start, end
        end -= pd.DateOffset(months=1)
    sys.exit("ERROR: no matched-month pair found in the data.")


def main():
    ap = argparse.ArgumentParser(
        description="Matched-month YoY employed-by-sex change (NSA), with the "
                    "published population-control effect subtracted when the "
                    "window straddles the Jan-2026 break.")
    ap.add_argument("--month", default=None,
                    help="end month YYYY-MM (default: latest with a "
                         "prior-year match); compares against same month "
                         "one year earlier")
    ap.add_argument("--min-base", type=float, default=500.0,
                    help="minimum |adjusted Both-sexes change| in thousands "
                         "for shares to be meaningful (default 500)")
    bls_client.add_client_args(ap)
    args = ap.parse_args()

    df = bls_client.fetch(list(reg.EMPLOYED_BY_SEX_NSA), refresh=args.refresh)
    reg.check_break_footnote(df)
    w = bls_client.to_wide(df, reg.EMPLOYED_BY_SEX_NSA)
    start, end = pick_window(w, args.month)

    straddles = reg.crosses_break(start, end)
    print("\n" + "#" * 62)
    print(f"# YoY window: {start:%Y-%m} -> {end:%Y-%m}  (NSA, matched months)")
    if straddles:
        print("# Window straddles the Jan-2026 break once -> BLS Table B")
        print("# subtraction applies. Adjusted figures below are valid.")
    else:
        print("# Window does NOT straddle the Jan-2026 break.")
        print("# No adjustment applied; raw is already basis-consistent.")
    print("#" * 62)

    print(f"\n  {'':12s}{'RAW YoY':>12s}{'pop-ctl effect':>16s}{'ADJUSTED YoY':>14s}")
    raw, adj = {}, {}
    for c in COLS:
        raw[c] = w.loc[end, c] - w.loc[start, c]
        eff = reg.POP_CTL_EFFECT_EMPLOYED_NSA[c] if straddles else 0
        adj[c] = raw[c] - eff
        print(f"  {c:12s}{raw[c]:>+11,.0f}k{eff:>+15,.0f}k{adj[c]:>+13,.0f}k")

    use = adj if straddles else raw
    label = "ADJUSTED" if straddles else "RAW"
    base = use["Both sexes"]
    if abs(base) >= args.min_base:
        print(f"\n  {label} women share of net YoY change: "
              f"{use['Women'] / base * 100:5.1f}%")
        print(f"  {label} men   share of net YoY change: "
              f"{use['Men'] / base * 100:5.1f}%")
    else:
        print(f"\n  {label} net change in Both sexes is {base:+,.0f}k -- "
              f"smaller than {args.min_base:,.0f}k, so shares of it are")
        print("  undefined for practical purposes (a near-zero base makes any")
        print("  share arbitrarily large). Quote the level changes above "
              "instead.")

    print("\n" + "=" * 62)
    print("READ: if a meaningful adjusted YoY women's share lands near the")
    print("~60% from the clean Dec-2023 -> Dec-2025 window, the headline is")
    print("confirmed and current. If the net change is too small to divide")
    print("by, say so -- do not manufacture a share. CPS monthly changes")
    print("carry wide confidence intervals; treat a few points of share")
    print("difference as noise, not signal.")
    print("=" * 62)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Employed by industry x sex, entirely inside the CPS (never mixing in CES).

Port of scripts/pull_industry_by_sex.py to the BLS API. Shows, for each
confirmed industry trio in series_registry.INDUSTRY_GROUPS:

  - the standing female SHARE of the industry (composition), and
  - the female share of the CHANGE since the baseline (growth decomposition),

reported around the Jan-2026 population-control break, never across it.
The pre-break segment runs baseline -> Dec-2025; the post-break segment runs
Jan-2026 -> latest, entirely on the new population basis.

To add finer industry trios, extend INDUSTRY_GROUPS in series_registry.py --
only publish from a trio after it passes the Men+Women=Both check printed here.

Run from anywhere:
    python v2/industry_by_sex.py [--baseline 2023-12] [-o out.csv] [--refresh]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bls_client
import series_registry as reg


def series_at(df: pd.DataFrame, sid: str, dt: pd.Timestamp) -> float | None:
    sub = df[(df["series_id"] == sid) & (df["date"] == dt)]
    return None if sub.empty else float(sub["value"].iloc[0])


def analyze_group(df, name, ids, baseline, latest):
    both_id, men_id, women_id = ids["both"], ids["men"], ids["women"]
    have = set(df["series_id"].unique())
    missing = [s for s in (both_id, men_id, women_id) if s not in have]
    if missing:
        print(f"\n[SKIP] {name}: no data returned for: {missing}")
        return

    def trio(dt):
        return (series_at(df, both_id, dt),
                series_at(df, men_id, dt),
                series_at(df, women_id, dt))

    print(f"\n{'=' * 66}\n{name}\n{'=' * 66}")
    print(f"  series: both={both_id} men={men_id} women={women_id}")

    # additivity check at latest (signed residual; |err| <= 5k rounding band)
    bL, mL, wL = trio(latest)
    if None not in (bL, mL, wL):
        err = (mL + wL) - bL
        print(f"  additivity (latest): men+women-both = {err:+.0f}k "
              f"({'OK' if abs(err) <= 5 else 'CHECK -- exceeds rounding'})")
        print(f"  female SHARE of the industry (latest): {wL / bL * 100:5.1f}%")

    # growth decomposition, split AT the break
    b0, m0, w0 = trio(baseline)
    bpre, mpre, wpre = trio(reg.PRE_BREAK_END)
    if None not in (b0, m0, w0, bpre, mpre, wpre):
        dW_pre, dM_pre, dB_pre = wpre - w0, mpre - m0, bpre - b0
        print(f"\n  PRE-BREAK segment ({baseline:%Y-%m} -> "
              f"{reg.PRE_BREAK_END:%Y-%m}, clean):")
        print(f"    women change: {dW_pre:>+7,.0f}k")
        print(f"    men   change: {dM_pre:>+7,.0f}k")
        print(f"    both  change: {dB_pre:>+7,.0f}k")
        if dB_pre != 0:
            print(f"    women share of net industry growth: "
                  f"{dW_pre / dB_pre * 100:5.1f}%")

    b_brk, m_brk, w_brk = trio(reg.BREAK_MONTH)
    if None not in (bL, mL, wL, b_brk, m_brk, w_brk):
        dW_post, dM_post, dB_post = wL - w_brk, mL - m_brk, bL - b_brk
        print(f"\n  POST-BREAK segment ({reg.BREAK_MONTH:%Y-%m} -> "
              f"{latest:%Y-%m}, new pop base):")
        print(f"    women change: {dW_post:>+7,.0f}k")
        print(f"    men   change: {dM_post:>+7,.0f}k")
        print(f"    both  change: {dB_post:>+7,.0f}k")
    else:
        print(f"\n  [POST-BREAK segment skipped: no data at "
              f"{reg.BREAK_MONTH:%Y-%m} or {latest:%Y-%m}]")


def main():
    ap = argparse.ArgumentParser(
        description="Employed by industry x sex (CPS), segmented at the "
                    "Jan-2026 population-control break.")
    ap.add_argument("--baseline", default=reg.DEFAULT_BASELINE,
                    help=f"baseline month YYYY-MM (default {reg.DEFAULT_BASELINE})")
    ap.add_argument("-o", "--out",
                    help="output CSV (default <repo>/v2/output/industry_by_sex.csv)")
    bls_client.add_client_args(ap)
    args = ap.parse_args()

    try:
        baseline = pd.to_datetime(args.baseline + "-01")
    except ValueError:
        sys.exit(f"ERROR: --baseline must be YYYY-MM, got {args.baseline!r}")

    all_ids = [sid for trio in reg.INDUSTRY_GROUPS.values()
               for sid in trio.values()]
    df = bls_client.fetch(all_ids, refresh=args.refresh)
    reg.check_break_footnote(df)
    latest = df["date"].max()

    print("\n" + "#" * 66)
    print("# DEFINITIONAL NOTE")
    print("# CPS industry is at the MAJOR GROUP level. 'Education and health")
    print("# services' is BROADER than the CES 'Health care and social")
    print("# assistance' from the NFP piece: it includes education. Report")
    print("# these as different measures. Do not equate them in prose.")
    print("#" * 66)

    # tidy monthly panel, legacy-compatible layout (date + series-id columns)
    panel = df.pivot(index="date", columns="series_id", values="value")
    panel = panel[sorted(panel.columns)].sort_index()
    panel = panel[panel.index >= baseline]
    if panel.empty:
        sys.exit(f"ERROR: no observations on or after baseline {args.baseline}; "
                 f"latest available month is {latest:%Y-%m}.")
    out_path = bls_client.resolve_out(args.out, "industry_by_sex.csv")
    panel.to_csv(out_path, float_format="%.0f", encoding="utf-8-sig")
    print(f"\nWrote tidy panel: {out_path}")

    for name, ids in reg.INDUSTRY_GROUPS.items():
        analyze_group(df, name, ids, baseline, latest)

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

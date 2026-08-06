#!/usr/bin/env python3
"""Employment level by sex, segmented AT the Jan-2026 population-control break.

Merged port of scripts/pull_employment_by_sex.py and
scripts/employment_by_sex_clean.py to the BLS API. No population-control
arithmetic; the window is split at the seam and never summed across it:

  SEGMENT 1  baseline -> Dec-2025   (entirely PRE-break: clean, no adjustment)
             Reported NSA Dec-to-Dec so seasonality nets out, and SA for check.
  SEGMENT 2  Jan-2026 -> latest     (entirely POST-break, new population base)
             Current readout only. NOT added to Segment 1.

Fixes vs the legacy scripts: the post-break segment starts at Jan-2026, so it
sits wholly on the new population basis (the legacy clean script started it at
Dec-2025, dragging the entire break step into the "post-break" number and
flipping its sign). No cross-break change columns are exported by default.

--demo-subtraction derives, from the data, why subtracting the published
population-control effect from a cross-break change is not a clean fix
(retiring the legacy employment_by_sex_adjusted.py).

Run from anywhere:
    python v2/employment_by_sex.py [--baseline 2023-12] [-o out.csv]
        [--change-window 2024-01:latest] [--demo-subtraction] [--refresh]
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


def segment(w: pd.DataFrame, start, end, title: str) -> dict | None:
    print(f"\n{'-' * 60}\n{title}\n  {start:%Y-%m} -> {end:%Y-%m}\n{'-' * 60}")
    if start not in w.index or end not in w.index:
        print("  endpoint missing on this basis.")
        return None
    ch = {c: w.loc[end, c] - w.loc[start, c] for c in COLS}
    for c in COLS:
        print(f"    {c:12s}: {ch[c]:>+8,.0f}k")
    if ch["Both sexes"] != 0:
        print(f"    women share of net growth: {ch['Women'] / ch['Both sexes'] * 100:5.1f}%")
        print(f"    men   share of net growth: {ch['Men'] / ch['Both sexes'] * 100:5.1f}%")
    return ch


def change_window(sa, nsa, spec: str) -> None:
    """Explicit change table for an arbitrary window; warns if it crosses
    the break rather than refusing (the warning is the point)."""
    try:
        start_s, end_s = spec.split(":")
        start = pd.to_datetime(start_s + "-01")
        end = nsa.index.max() if end_s == "latest" else pd.to_datetime(end_s + "-01")
    except ValueError:
        sys.exit(f"ERROR: --change-window must be YYYY-MM:YYYY-MM or "
                 f"YYYY-MM:latest, got {spec!r}")
    print(f"\n{'=' * 60}\nEXPLICIT CHANGE WINDOW (requested)\n{'=' * 60}")
    reg.warn_if_crosses_break(start, end, "change-window")
    segment(nsa, start, end, "NSA")
    segment(sa, start, end, "SA")


def demo_subtraction(nsa: pd.DataFrame, baseline, latest) -> None:
    """Derive why 'subtract the published population-control effect' is not a
    clean fix for a cross-break window (all numbers computed, none hardcoded)."""
    need = [baseline, reg.PRE_BREAK_END, reg.BREAK_MONTH, latest]
    if any(m not in nsa.index for m in need):
        print("\n[demo-subtraction skipped: a required month is missing]")
        return
    print(f"\n{'#' * 64}")
    print("# WHY SUBTRACTING THE PUBLISHED EFFECT IS NOT A CLEAN FIX")
    print("# (NSA basis -- the basis the published effect is defined on)")
    print(f"{'#' * 64}")
    print(f"  window: {baseline:%Y-%m} -> {latest:%Y-%m}")
    print(f"  {'':12s}{'naive':>10s}{'effect':>10s}{'adjusted':>10s}"
          f"{'seg1+seg2':>11s}{'residual':>10s}")
    for c in COLS:
        naive = nsa.loc[latest, c] - nsa.loc[baseline, c]
        effect = reg.POP_CTL_EFFECT_EMPLOYED_NSA[c]
        adjusted = naive - effect
        seg1 = nsa.loc[reg.PRE_BREAK_END, c] - nsa.loc[baseline, c]
        seg2 = nsa.loc[latest, c] - nsa.loc[reg.BREAK_MONTH, c]
        residual = adjusted - (seg1 + seg2)
        print(f"  {c:12s}{naive:>+9,.0f}k{effect:>+9,.0f}k{adjusted:>+9,.0f}k"
              f"{seg1 + seg2:>+10,.0f}k{residual:>+9,.0f}k")
    print("""
  Reading the table: adjusted = naive - published effect, yet it still does
  NOT equal the sum of the two within-basis segment changes. The residual is
  the Dec-2025 -> Jan-2026 seam month net of the control effect -- ordinary
  December-to-January (seasonal) movement that the subtraction leaves inside
  the "adjusted" figure. The seam month is being counted once inside BLS's
  effect (which is defined ON that month) and once as retained seasonal
  movement, so the adjusted number sits on no consistent basis. Report the
  two segments separately instead.""")


def main():
    ap = argparse.ArgumentParser(
        description="Employment by sex (CPS), segmented at the Jan-2026 "
                    "population-control break.")
    ap.add_argument("--baseline", default=reg.DEFAULT_BASELINE,
                    help=f"segment-1 start YYYY-MM (default {reg.DEFAULT_BASELINE})")
    ap.add_argument("-o", "--out",
                    help="output CSV (default <repo>/v2/output/employment_by_sex.csv)")
    ap.add_argument("--change-window", metavar="START:END",
                    help="also print changes over an explicit window "
                         "(YYYY-MM:YYYY-MM or YYYY-MM:latest); warns if it "
                         "crosses the break")
    ap.add_argument("--demo-subtraction", action="store_true",
                    help="derive why subtracting the published population-"
                         "control effect double-counts the seam month")
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
    latest = df["date"].max()

    if baseline not in nsa.index:
        sys.exit(f"ERROR: baseline {args.baseline} not in the data "
                 f"({nsa.index.min():%Y-%m} .. {nsa.index.max():%Y-%m}).")

    print("\n" + "#" * 60)
    print("# CLEAN SEGMENTED VIEW - no population-control arithmetic")
    print("# Each segment sits on ONE population basis. Never sum across")
    print("# the Jan-2026 seam.")
    print("#" * 60)

    print("\n" + "=" * 60)
    print("SEGMENT 1  (PRE-BREAK, CLEAN - this is your headline window)")
    print("=" * 60)
    s1_nsa = segment(nsa, baseline, reg.PRE_BREAK_END,
                     "NSA, Dec-to-Dec (seasonality nets out) [PRIMARY]")
    segment(sa, baseline, reg.PRE_BREAK_END, "SA (robustness check)")

    print("\n" + "=" * 60)
    print("SEGMENT 2  (POST-BREAK, new pop base - report SEPARATELY)")
    print("=" * 60)
    segment(nsa, reg.BREAK_MONTH, latest, "NSA, Jan-2026 -> latest")
    segment(sa, reg.BREAK_MONTH, latest, "SA, Jan-2026 -> latest")

    # tidy export: levels on both bases + segment marker + within-segment
    # changes (change vs the segment's own start month, never across the seam)
    out = pd.concat([sa.add_suffix(" (SA)"), nsa.add_suffix(" (NSA)")], axis=1)
    out = out[out.index >= baseline].sort_index()
    out.index.name = "date"
    seg_col = pd.Series("pre-break", index=out.index)
    seg_col[out.index >= reg.BREAK_MONTH] = "post-break"
    chg = {}
    for col in list(out.columns):
        pre = out.loc[out.index < reg.BREAK_MONTH, col]
        post = out.loc[out.index >= reg.BREAK_MONTH, col]
        chg[col + " chg (segment)"] = pd.concat([
            pre - (pre.loc[baseline] if baseline in pre.index else pd.NA),
            post - (post.loc[reg.BREAK_MONTH] if reg.BREAK_MONTH in post.index else pd.NA),
        ])
    out = pd.concat([out, pd.DataFrame(chg)], axis=1)
    out["segment"] = seg_col
    out_path = bls_client.resolve_out(args.out, "employment_by_sex.csv")
    out.to_csv(out_path, float_format="%.0f", encoding="utf-8-sig")
    print(f"\nWrote: {out_path}")

    if args.change_window:
        change_window(sa, nsa, args.change_window)
    if args.demo_subtraction:
        demo_subtraction(nsa, baseline, latest)

    print("\n" + "=" * 60)
    print("HOW TO STATE IT:")
    if s1_nsa and s1_nsa["Both sexes"] != 0:
        ws = s1_nsa["Women"] / s1_nsa["Both sexes"] * 100
        print(f"  Over the clean pre-break window ({baseline:%Y-%m} to "
              f"{reg.PRE_BREAK_END:%Y-%m}), women")
        print(f"  were {ws:.0f}% of net employment growth (NSA Dec-to-Dec).")
    print("  The Jan-2026 population controls create a break; we report the")
    print("  months after it separately and do not sum across it. Cite BLS")
    print("  empsit_03062026 Table A/B in prose as the reason for the seam.")
    print("=" * 60)


if __name__ == "__main__":
    main()

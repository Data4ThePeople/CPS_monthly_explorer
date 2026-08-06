#!/usr/bin/env python3
"""Figures behind the multiple-jobholders chart (BLS series LNU02026625).

Port of scripts/multiple_jobholders_numbers.py to the BLS API.
Series LNU02026625 = Employed, multiple jobholders, primary job full time,
secondary job part time, 16+, Both Sexes, NSA, thousands (mjhs code 02).

Prints latest / 2008-09-window peak / all-time peak / gap for both the
12-month moving average (the chart's bold line) and the raw monthly series.

Data hazards handled here (the legacy script ignored both): Oct-2025 was
never collected, so the moving average is computed on a gap-aware monthly
calendar -- a "12-month" window that touches the hole is reported as NaN
rather than passed off as a 12-month average of 12 observations spanning 13
months. Windows that span the Jan-2026 population-control break mix two
population bases and are flagged. Use --allow-gap to bridge the hole with an
11-of-12 average, loudly caveated.

Run from anywhere:
    python v2/multiple_jobholders.py [-o out.csv] [--allow-gap] [--refresh]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bls_client
import series_registry as reg

# Peak-search band for the recession-era comparison. The NBER contraction ran
# Dec-2007 .. Jun-2009; the band is wider so the smoothed line's peak (which
# lags the raw peak) is not clipped.
REC_START, REC_END = "2007-12", "2009-12"


def main():
    ap = argparse.ArgumentParser(
        description="Numbers behind the multiple-jobholders chart "
                    "(12-month moving average and raw monthly).")
    ap.add_argument("--series", default=reg.MULTIPLE_JOBHOLDERS_FT_PT,
                    help=f"series id (default {reg.MULTIPLE_JOBHOLDERS_FT_PT})")
    ap.add_argument("--rec-start", default=REC_START,
                    help=f"recession window start YYYY-MM (default {REC_START})")
    ap.add_argument("--rec-end", default=REC_END,
                    help=f"recession window end YYYY-MM (default {REC_END})")
    ap.add_argument("--allow-gap", action="store_true",
                    help="let the moving average bridge the Oct-2025 hole "
                         "with 11 of 12 months (caveat loudly when quoting)")
    ap.add_argument("-o", "--out",
                    help="output CSV (default <repo>/v2/output/multiple_jobholders.csv)")
    bls_client.add_client_args(ap)
    args = ap.parse_args()

    sid = args.series.strip()
    df = bls_client.fetch([sid], refresh=args.refresh)
    reg.check_break_footnote(df)

    s = df.set_index("date")["value"]
    # complete monthly calendar, so the hole is an explicit NaN, not a
    # silently skipped position
    full_idx = pd.date_range(s.index.min(), s.index.max(), freq="MS")
    s = s.reindex(full_idx)
    n_missing = int(s.isna().sum())
    if n_missing:
        gaps = ", ".join(f"{dt:%Y-%m}" for dt in s.index[s.isna()])
        print(f"[note] {n_missing} month(s) missing from the series: {gaps}")

    min_periods = 11 if args.allow_gap else 12
    if args.allow_gap:
        print("[note] --allow-gap: windows touching a missing month average "
              "the 11 present values. Caveat any quoted figure accordingly.")
    ma12 = s.rolling(12, min_periods=min_periods).mean()

    # flags: does the trailing 12-month window contain the gap / the break?
    idx = s.index
    win_start = idx - pd.DateOffset(months=11)
    spans_gap = pd.Series((win_start <= reg.GAP_MONTH) & (idx >= reg.GAP_MONTH),
                          index=idx)
    spans_break = pd.Series(
        (win_start < reg.BREAK_MONTH) & (idx >= reg.BREAK_MONTH), index=idx)
    n_mixed = int((spans_break & ma12.notna()).sum())
    if n_mixed:
        print(f"[note] {n_mixed} moving-average window(s) mix population "
              f"bases across the Jan-2026 break -- flagged in the CSV.")

    d = pd.DataFrame({
        "value": s, "ma12": ma12,
        "spans_gap": spans_gap, "spans_break": spans_break,
    })
    d.index.name = "date"
    out_path = bls_client.resolve_out(args.out, "multiple_jobholders.csv")
    d.to_csv(out_path, float_format="%.1f", encoding="utf-8-sig")
    print(f"Wrote: {out_path}")

    def block(label, col):
        v = d[col].dropna()
        if v.empty:
            print(f"\n=== {label} ===\n  no defined values.")
            return
        latest_dt, latest_v = v.index[-1], v.iloc[-1]
        print(f"\n=== {label} ===")
        print(f"  latest defined ({latest_dt:%b %Y}):      {latest_v:,.0f} thousand")
        if latest_dt != d.index[-1]:
            print(f"    (later months exist but their window touches the "
                  f"Oct-2025 hole; the next fully-defined 12-month average "
                  f"arrives with Sep-2026 data)")
        rs = pd.Timestamp(args.rec_start + "-01")
        re_end = pd.Timestamp(args.rec_end + "-01")
        win = v[(v.index >= rs) & (v.index <= re_end)]
        if len(win):
            rec_dt, rec_v = win.idxmax(), win.max()
            print(f"  2008-09 window peak ({rec_dt:%b %Y}): {rec_v:,.0f} thousand")
            print(f"  latest minus 2008-09 peak:        {latest_v - rec_v:+,.0f} thousand")
        all_dt, all_v = v.idxmax(), v.max()
        print(f"  all-time peak ({all_dt:%b %Y}):      {all_v:,.0f} thousand")

    n_obs = int(s.notna().sum())
    print(f"\nSeries {sid}: {n_obs} monthly obs, "
          f"{idx.min():%b %Y} to {idx.max():%b %Y}")
    block("12-MONTH MOVING AVERAGE  (bold line / 'trailing 12 months')", "ma12")
    block("RAW MONTHLY (NSA)  (thin line)", "value")

    print("\nFor the post, compare the 12-month-average latest against the "
          "12-month-average\n2008-09 peak -- that's the apples-to-apples "
          '"trailing 12 months" number.')


if __name__ == "__main__":
    main()

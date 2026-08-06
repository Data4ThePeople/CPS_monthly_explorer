#!/usr/bin/env python3
"""Verify the redistribution waterfall's six figures against the API, numerically.

Port of scripts/verify_waterfall_measure.py. The published waterfall chart
plots one Jan-2026-minus-Dec-2025 step per race group; this script recomputes
each step for BOTH the civilian noninstitutional population series and the
civilian labor force series, then checks the chart's plotted values against
the population column with a tolerance, printing PASS/FAIL per group and
exiting nonzero on any mismatch (the legacy script left the comparison to the
reader's eyeball and could not fail).

Measuring the Dec-2025 -> Jan-2026 step is a legitimate cross-break
measurement -- the step IS the break -- but the six values are differences,
not published series, and they need not net to zero; the residual is printed.

Run from anywhere:
    python v2/verify_waterfall.py [--tolerance 1] [--refresh]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bls_client
import series_registry as reg


def main():
    ap = argparse.ArgumentParser(
        description="Numerically verify the waterfall chart's six "
                    "Dec-2025 -> Jan-2026 population steps.")
    ap.add_argument("--tolerance", type=float, default=1.0,
                    help="max |difference| in thousands to count as a match "
                         "(default 1)")
    bls_client.add_client_args(ap)
    args = ap.parse_args()

    ids = [sid for _, pop, lf in reg.WATERFALL_GROUPS for sid in (pop, lf)]
    df = bls_client.fetch(ids, start_year=2025, refresh=args.refresh)

    def step(sid):
        s = df[df["series_id"] == sid].set_index("date")["value"]
        if reg.PRE_BREAK_END not in s.index or reg.BREAK_MONTH not in s.index:
            return None
        return s.loc[reg.BREAK_MONTH] - s.loc[reg.PRE_BREAK_END]

    print(f"\n{'Group':<20}{'POPULATION step':>17}{'LABOR FORCE step':>18}"
          f"{'chart value':>13}{'verdict':>9}")
    print("-" * 77)
    failures = 0
    pop_total = 0.0
    for label, pop_id, lf_id in reg.WATERFALL_GROUPS:
        ps, ls = step(pop_id), step(lf_id)
        chart = reg.WATERFALL_CHART_VALUES[label]
        if ps is None:
            verdict = "NO DATA"
            failures += 1
        elif abs(ps - chart) <= args.tolerance:
            verdict = "PASS"
            pop_total += ps
        else:
            verdict = "FAIL"
            failures += 1
        ps_s = f"{ps:+,.0f}" if ps is not None else "n/a"
        ls_s = f"{ls:+,.0f}" if ls is not None else "n/a"
        print(f"{label:<20}{ps_s:>17}{ls_s:>18}{chart:>+13,}{verdict:>9}")

    print("-" * 77)
    chart_sum = sum(reg.WATERFALL_CHART_VALUES.values())
    print(f"Sum of the six chart values: {chart_sum:+,.0f}k -- the six race "
          f"groups are not a partition of the")
    print("population, so the steps need not net to zero. Disclose the "
          "residual if the chart implies a swap.")

    if failures:
        print(f"\n{failures} group(s) did NOT match the POPULATION step "
              f"within {args.tolerance:g}k.")
        print("Either the chart plots something else (check the LABOR FORCE "
              "column) or the data was revised.")
        sys.exit(1)
    print(f"\nAll six chart values match the POPULATION step within "
          f"{args.tolerance:g}k -> the subtitle 'population count' is CORRECT.")


if __name__ == "__main__":
    main()

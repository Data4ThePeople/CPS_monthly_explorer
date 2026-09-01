#!/usr/bin/env python3
"""Print the labor force flow figures used in the explorer and intro page copy.

The copy in analysis/explorer-copy/labor-force-flows-copy.md quotes a specific
month. Re-run this after each Employment Situation release and update the four
numbers rather than letting them go stale.

    python v2/flows_copy.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bls_client

FLOWS = {
    "Employed -> not in labor force": "LNS17800000",
    "Employed -> unemployed":         "LNS17400000",
    "Not in labor force -> employed": "LNS17200000",
    "Unemployed -> employed":         "LNS17100000",
}

if __name__ == "__main__":
    df = bls_client.fetch(list(FLOWS.values()))
    w = df.pivot_table(index="date", columns="series_id", values="value")
    w.columns = [{v: k for k, v in FLOWS.items()}[c] for c in w.columns]
    w = w.sort_index()
    last = w.dropna(how="all").index[-1]
    r = w.loc[last]
    print(f"Labor force flows, seasonally adjusted, {last:%B %Y}\n")
    for k in FLOWS:
        print(f"  {k:32s} {r[k]*1000:>12,.0f}")
    print(f"\n  leaving work for the sidelines vs for unemployment: "
          f"{r['Employed -> not in labor force']/r['Employed -> unemployed']:.1f}x")
    print(f"  starting work from outside the labor force vs from unemployment: "
          f"{r['Not in labor force -> employed']/r['Unemployed -> employed']:.1f}x")
    print(f"\n  flows are published monthly from February 1990, not 1948.")

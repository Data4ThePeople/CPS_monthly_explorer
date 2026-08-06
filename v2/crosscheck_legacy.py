#!/usr/bin/env python3
"""Cross-check v2 (API-sourced) CSVs against the shipped legacy outputs.

The legacy CSVs in <repo>/output/ were produced from the downloaded flat
file; the v2 CSVs come from the API. For the same series and months the
values should match exactly -- any difference is either a real BLS revision
published after the flat file was downloaded (expected only in recent
months) or a bug. This script aligns each pair on date, compares the shared
LEVEL columns (derived columns like MoM are excluded: v2 intentionally masks
the gap-spanning diff), and reports per-column max |difference| and the
mismatching months.

Exit 0 only on exact match everywhere; --allow-revisions downgrades
mismatches to warnings (use it after eyeballing that the diffs are confined
to recent months, i.e. revisions rather than bugs).

Run from anywhere (after the v2 scripts have written their CSVs):
    python v2/crosscheck_legacy.py [--allow-revisions]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bls_client

LEGACY_OUT = bls_client.REPO_ROOT / "output"
V2_OUT = bls_client.OUT_DIR

PAIRS = [
    # (v2 file, legacy file, columns to compare)
    ("employment_by_sex.csv", "employment_by_sex_clean.csv",
     ["Both sexes (SA)", "Men (SA)", "Women (SA)",
      "Both sexes (NSA)", "Men (NSA)", "Women (NSA)"]),
    ("industry_by_sex.csv", "industry_by_sex.csv",
     ["LNU02034574", "LNU02037841", "LNU02037935"]),
    ("men_monthly_path.csv", "men_monthly_path.csv",
     ["Both sexes", "Men", "Women"]),
]


def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", parse_dates=["date"])
    return df.set_index("date")


def main():
    ap = argparse.ArgumentParser(
        description="Compare v2 API-sourced CSVs against the shipped "
                    "legacy flat-file outputs.")
    ap.add_argument("--allow-revisions", action="store_true",
                    help="report mismatches but exit 0 (use once diffs are "
                         "confirmed to be BLS revisions, not bugs)")
    args = ap.parse_args()

    any_mismatch = False
    for v2_name, legacy_name, cols in PAIRS:
        v2_path, legacy_path = V2_OUT / v2_name, LEGACY_OUT / legacy_name
        print(f"\n=== {v2_name}  vs  legacy {legacy_name} ===")
        missing = [p for p in (v2_path, legacy_path) if not p.is_file()]
        if missing:
            print("  SKIP: missing " + ", ".join(str(p) for p in missing))
            continue
        v2, legacy = load(v2_path), load(legacy_path)
        shared = v2.index.intersection(legacy.index)
        print(f"  overlapping months: {len(shared)} "
              f"({shared.min():%Y-%m} .. {shared.max():%Y-%m})")
        for col in cols:
            if col not in v2.columns or col not in legacy.columns:
                print(f"  {col:22s} SKIP (column missing)")
                any_mismatch = True
                continue
            diff = (v2.loc[shared, col] - legacy.loc[shared, col]).astype(float)
            bad = diff[diff != 0]
            if bad.empty:
                print(f"  {col:22s} OK (exact match on all months)")
            else:
                any_mismatch = True
                months = ", ".join(f"{dt:%Y-%m}({v:+.0f})"
                                   for dt, v in bad.items())
                print(f"  {col:22s} {len(bad)} mismatching month(s), "
                      f"max |diff| {bad.abs().max():.0f}k: {months}")

    print()
    if any_mismatch:
        if args.allow_revisions:
            print("Mismatches found; --allow-revisions set, exiting 0. "
                  "Confirm the months above are recent (revisions).")
            return
        print("Mismatches found. If they are confined to recent months they "
              "are BLS revisions published")
        print("after the flat file was downloaded; re-run with "
              "--allow-revisions once confirmed.")
        sys.exit(1)
    print("All shared columns match exactly on all overlapping months.")


if __name__ == "__main__":
    main()

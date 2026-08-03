#!/usr/bin/env python3
"""
multiple_jobholders_numbers.py -- Pull the exact figures for the
multiple-jobholders chart (BLS series LNU02026625) from the local LN data.

Series LNU02026625 = Employed, multiple jobholders, primary job full time,
secondary job part time, 16+, Both Sexes, not seasonally adjusted, in
thousands. (mjhs code 02, per the ln.mjhs mapping file.)

Prints, for the 12-MONTH MOVING AVERAGE (the bold line in the chart, which is
what "on a trailing 12-month basis" refers to):
  * the latest value
  * the peak during the 2008-2009 recession window
  * the all-time peak of the smoothed line (in case it's not "now")
  * the gap between latest and the 2008-2009 peak
and the same for the RAW monthly series, so you can pick the comparison you
actually want to make and quote a number you can defend from the data.

USAGE:
  python3 scripts/multiple_jobholders_numbers.py
  python3 scripts/multiple_jobholders_numbers.py --series LNU02026625

Requires: pandas. Reads ln.data.1.AllData (.txt suffix fine).
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# --- Repo layout -------------------------------------------------------------
# <repo>/scripts/<this file>, <repo>/data (BLS flat files), <repo>/output
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
OUT_DIR = REPO_ROOT / "output"


SERIES = "LNU02026625"
REC_START, REC_END = "2007-12", "2009-12"  # NBER 2008-09 recession window


def find_data(folder):
    for c in ("ln.data.1.AllData", "ln.data.1.AllData.txt"):
        if (folder / c).exists():
            return folder / c
    hits = sorted(folder.glob("ln.data*"))
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("-d", "--dir", default=str(DATA_DIR))
    ap.add_argument("--series", default=SERIES)
    ap.add_argument("--rec-start", default=REC_START,
                    help="recession window start YYYY-MM (default 2007-12)")
    ap.add_argument("--rec-end", default=REC_END,
                    help="recession window end YYYY-MM (default 2009-12)")
    args = ap.parse_args()

    folder = Path(args.dir).expanduser()
    dp = find_data(folder)
    if dp is None:
        sys.exit(f"ERROR: no ln.data.* file in {folder}")

    sid = args.series.strip()
    print(f"Scanning {dp.name} for {sid} ...")
    rows = []
    for chunk in pd.read_csv(dp, sep="\t", dtype=str, chunksize=1_000_000,
                             keep_default_na=False, na_values=[]):
        chunk.columns = [c.strip() for c in chunk.columns]
        chunk["series_id"] = chunk["series_id"].str.strip()
        hit = chunk[chunk["series_id"] == sid]
        if len(hit):
            rows.append(hit)
    if not rows:
        sys.exit(f"ERROR: {sid} not found in the data file. Check the ID "
                 f"in the chart footer.")
    d = pd.concat(rows, ignore_index=True)
    d["period"] = d["period"].str.strip()
    d = d[d["period"].str.match(r"M(0[1-9]|1[0-2])$")]      # monthly only
    d["value"] = pd.to_numeric(d["value"].str.strip(), errors="coerce")
    d["date"] = pd.to_datetime(d["year"].str.strip() + "-"
                               + d["period"].str[1:] + "-01")
    d = d.dropna(subset=["value"]).sort_values("date").reset_index(drop=True)
    d["ma12"] = d["value"].rolling(12).mean()

    def block(label, col):
        s = d.dropna(subset=[col])
        latest = s.iloc[-1]
        # recession window peak
        rs = pd.Timestamp(args.rec_start + "-01")
        re_ = pd.Timestamp(args.rec_end + "-01")
        win = s[(s["date"] >= rs) & (s["date"] <= re_)]
        rec_peak = win.loc[win[col].idxmax()] if len(win) else None
        allpeak = s.loc[s[col].idxmax()]
        print(f"\n=== {label} ===")
        print(f"  latest ({latest['date']:%b %Y}):            "
              f"{latest[col]:,.0f} thousand")
        if rec_peak is not None:
            print(f"  2008-09 window peak ({rec_peak['date']:%b %Y}): "
                  f"{rec_peak[col]:,.0f} thousand")
            gap = latest[col] - rec_peak[col]
            print(f"  latest minus 2008-09 peak:        "
                  f"{gap:+,.0f} thousand")
        print(f"  all-time peak ({allpeak['date']:%b %Y}):     "
              f"{allpeak[col]:,.0f} thousand")

    print(f"\nSeries {sid}: {len(d)} monthly obs, "
          f"{d['date'].min():%b %Y} to {d['date'].max():%b %Y}")
    block("12-MONTH MOVING AVERAGE  (bold line / 'trailing 12 months')", "ma12")
    block("RAW MONTHLY (NSA)  (thin line)", "value")

    print("\nFor the post, compare the 12-month-average latest against the "
          "12-month-average\n2008-09 peak -- that's the apples-to-apples "
          '"trailing 12 months" number.')


if __name__ == "__main__":
    main()

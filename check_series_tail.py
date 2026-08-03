#!/usr/bin/env python3
"""
Pull the tail of a single BLS CPS (LN) series from the local flat-file database.

Default: LNS11000003 (Civilian labor force, White, 16+, Both Sexes, SA)
Prints the last N monthly observations so you can see whether the chart's
final point is a real value or a partial/preliminary/artifact print.

Usage:
    python3 check_series_tail.py
    python3 check_series_tail.py LNS11000003 24
    python3 check_series_tail.py LNU02026625 36

Point LN_DIR at wherever your flat files live (default ~/Desktop/ln).
"""

import os
import sys

LN_DIR = os.path.expanduser("~/Desktop/ln")
DATA_FILE = os.path.join(LN_DIR, "ln.data.1.AllData.txt")

series_id = sys.argv[1].strip() if len(sys.argv) > 1 else "LNS11000003"
n_tail = int(sys.argv[2]) if len(sys.argv) > 2 else 18

if not os.path.exists(DATA_FILE):
    sys.exit(f"Cannot find {DATA_FILE}\n"
             f"Edit LN_DIR at the top of this script to point at your ln folder.")

# The AllData file is tab-delimited with columns:
#   series_id   year   period   value   footnote_codes
# period is M01..M12 (monthly) or M13 (annual average). We keep monthly only.
rows = []
header_seen = False
with open(DATA_FILE, "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 4:
            continue
        sid = parts[0].strip()
        if sid == "series_id":
            header_seen = True
            continue
        # Exact match only. BLS pads series_id with trailing spaces (stripped
        # above). Reject near-matches that carry a suffix, e.g. the quarterly
        # variant "LNS11300003Q", which startswith-style matching would wrongly
        # include. We want ONLY the exact monthly code the user asked for.
        if sid != series_id:
            continue
        year = parts[1].strip()
        period = parts[2].strip()
        value = parts[3].strip()
        foot = parts[4].strip() if len(parts) > 4 else ""
        if period == "M13":  # annual average, skip
            continue
        rows.append((year, period, value, foot))

if not rows:
    sys.exit(f"No rows found for {series_id}. "
             f"Check the series ID (header row seen: {header_seen}).")

# Sort chronologically and take the tail
rows.sort(key=lambda r: (int(r[0]), r[1]))
tail = rows[-n_tail:]

print(f"\nSeries: {series_id}")
print(f"Total monthly observations in file: {len(rows)}")
print(f"Showing last {len(tail)} months\n")

# Decide display precision. Rate series (participation, unemployment rate,
# emp-pop ratio) run 0-100 and carry meaningful tenths. Level series run in
# the thousands. Sniff the magnitude of the most recent numeric value to pick
# decimals so we never crush a rate's tenths down to a flat integer.
def _num(v):
    try:
        return float(v)
    except ValueError:
        return None

recent_vals = [n for n in (_num(r[2]) for r in tail) if n is not None]
is_rate = bool(recent_vals) and max(abs(v) for v in recent_vals) < 1000
decimals = 1 if is_rate else 0
vfmt = f"{{:,.{decimals}f}}"

print(f"{'Year':<6}{'Month':<7}{'Value':>14}{'  Footnote':<12}{'MoM change':>14}")
print("-" * 55)

prev = None
for year, period, value, foot in tail:
    v = _num(value)
    if v is not None:
        mom = f"{v - prev:+,.{decimals}f}" if prev is not None else ""
        prev = v
        vstr = vfmt.format(v)
    else:
        mom = ""
        vstr = value  # e.g. "-" for missing
    month = period.replace("M", "")
    print(f"{year:<6}{month:<7}{vstr:>14}{'  ' + (foot or '-'):<12}{mom:>14}")

print()

#!/usr/bin/env python3
"""
Print RAW lines from ln.data.1.AllData.txt for one series, with delimiters made
visible, so we can see the true column layout and why a rate is reading as an
integer.

Usage:
    python3 inspect_raw_lines.py                 # LNS11300003, last 6 lines
    python3 inspect_raw_lines.py LNS11300003 8
"""

import os
import sys

LN_DIR = os.path.expanduser("~/Desktop/ln")
DATA_FILE = os.path.join(LN_DIR, "ln.data.1.AllData.txt")

series_id = sys.argv[1].strip() if len(sys.argv) > 1 else "LNS11300003"
n_tail = int(sys.argv[2]) if len(sys.argv) > 2 else 6

if not os.path.exists(DATA_FILE):
    sys.exit(f"Cannot find {DATA_FILE}. Edit LN_DIR at the top of this script.")

# First, show the header line exactly as stored
print("=== HEADER LINE (raw, tabs shown as [TAB]) ===")
with open(DATA_FILE, "r", encoding="utf-8", errors="replace") as f:
    first = f.readline().rstrip("\n")
    print(repr(first))
    print("Visible:", first.replace("\t", "[TAB]"))
print()

# Collect matching lines
matches = []
with open(DATA_FILE, "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        # match on the series id at the very start of the line
        if line.startswith(series_id):
            matches.append(line.rstrip("\n"))

if not matches:
    sys.exit(f"No lines start with {series_id}.")

tail = matches[-n_tail:]
print(f"=== LAST {len(tail)} RAW LINES for {series_id} ===\n")
for ln in tail:
    print("RAW repr :", repr(ln))
    print("Tabs     :", ln.replace("\t", "[TAB]"))
    parts = ln.split("\t")
    print(f"Split on TAB -> {len(parts)} fields:")
    for i, p in enumerate(parts):
        print(f"    [{i}] {p!r}")
    print("-" * 60)

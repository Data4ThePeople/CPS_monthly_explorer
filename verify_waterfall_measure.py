#!/usr/bin/env python3
"""
Verify whether the redistribution waterfall's six figures are POPULATION or
LABOR FORCE. For each race group, print the Jan-2026 (minus Dec-2025) step for
BOTH the civilian noninstitutional population series and the civilian labor
force series, so we can match them against the chart values:

   White -5,635 | Black -631 | Two or more +3,245
   AIAN +1,420  | Asian +1,068 | NHOPI +393

If those match the POPULATION column, the subtitle "population count" is correct.

Series IDs (population = ...00000.../...0009.../...0003.../...0006 family;
labor force = ...11 or ...010 / 01... family). Verify each title as printed.

Usage: python3 verify_waterfall_measure.py
"""

import os

LN_DIR = os.path.expanduser("~/Desktop/ln")
DATA_FILE = os.path.join(LN_DIR, "ln.data.1.AllData.txt")

# (label, population_series_id, laborforce_series_id)
GROUPS = [
    ("White",              "LNU00000003", "LNU01000003"),
    ("Black",              "LNU00000006", "LNU01000006"),
    ("Asian",              "LNU00032183", "LNU01032183"),
    ("Two or more races",  "LNU00092154", "LNU01092154"),
    ("AIAN",               "LNU00035243", "LNU01035243"),
    ("NHOPI",              "LNU00035553", "LNU01035553"),
]

# Collect the Dec-2025 and Jan-2026 monthly values for every id we care about
wanted = set()
for _, pop, lf in GROUPS:
    wanted.add(pop); wanted.add(lf)

vals = {}  # (sid, year, period) -> value
with open(DATA_FILE, "r", encoding="utf-8", errors="replace") as f:
    f.readline()
    for line in f:
        sid = line.split("\t", 1)[0].strip()
        if sid in wanted:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 4:
                y, per, v = p[1].strip(), p[2].strip(), p[3].strip()
                if (y, per) in (("2025", "M12"), ("2026", "M01")):
                    try:
                        vals[(sid, y, per)] = float(v)
                    except ValueError:
                        pass

def step(sid):
    dec = vals.get((sid, "2025", "M12"))
    jan = vals.get((sid, "2026", "M01"))
    if dec is None or jan is None:
        return None
    return jan - dec

print(f"{'Group':<20}{'POPULATION step':>18}{'LABOR FORCE step':>20}")
print("-" * 58)
for label, pop, lf in GROUPS:
    ps = step(pop); ls = step(lf)
    ps_s = f"{ps:+,.0f}" if ps is not None else "n/a"
    ls_s = f"{ls:+,.0f}" if ls is not None else "n/a"
    print(f"{label:<20}{ps_s:>18}{ls_s:>20}")
print()
print("Chart plots: White -5,635 | Black -631 | Two+ +3,245 | AIAN +1,420 | Asian +1,068 | NHOPI +393")
print("If those match the POPULATION column -> subtitle 'population count' is CORRECT.")

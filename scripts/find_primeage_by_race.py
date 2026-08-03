#!/usr/bin/env python3
"""
Find the "Civilian noninstitutional population, 25-54 years, Both Sexes" series
for EACH race group, so we can test whether the Jan-2026 White prime-age drop
(-3,984) was offset by prime-age GAINS in other race groups (the "reclassified
to another race" hypothesis) or not.

Also grabs the same for 16+ per race, so we can compute prime-age SHARE per race
if wanted.

Usage:
    python3 scripts/find_primeage_by_race.py

Prints verified series_ids (with data check) to feed into check_series_tail.py.
"""

import os
import re
import glob

LN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      os.pardir, "data")
SERIES_FILE = os.path.join(LN_DIR, "ln.series")
DATA_FILE = os.path.join(LN_DIR, "ln.data.1.AllData.txt")

for cand in (SERIES_FILE, SERIES_FILE + ".txt"):
    if os.path.exists(cand):
        SERIES_FILE = cand
        break

WANT_AGES = {"25 to 54 years", "16 years and over"}
WANT_MEASURE = "Civilian noninstitutional population"


def load_tsv(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = [h.strip() for h in f.readline().rstrip("\n").split("\t")]
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < len(header):
                parts += [""] * (len(header) - len(parts))
            yield {header[i]: parts[i].strip() for i in range(len(header))}


def load_map(basename):
    path = os.path.join(LN_DIR, basename)
    if not os.path.exists(path) and os.path.exists(path + ".txt"):
        path += ".txt"
    if not os.path.exists(path):
        return {}
    rows = list(load_tsv(path))
    if not rows:
        return {}
    keys = list(rows[0].keys())
    code_col = keys[0]
    label_col = next((k for k in keys if "text" in k.lower()),
                     keys[1] if len(keys) > 1 else keys[0])
    return {r[code_col]: r[label_col] for r in rows}


race_map = load_map("ln.race")     # code -> race label (all groups)
age_map = load_map("ln.ages")
lfst_map = load_map("ln.lfst")
sexs_map = load_map("ln.sexs")

bothsex_codes = {c for c, l in sexs_map.items()
                 if l.strip().lower() in ("both sexes", "both")}

print("=== race codes available ===")
for c, l in sorted(race_map.items()):
    print(f"  {c} = {l}")
print()

# Collect one series per (race, age) for the population measure, plain title
results = {}  # (race_label, age_label) -> dict
for r in load_tsv(SERIES_FILE):
    age_label = age_map.get(r.get("ages_code", ""), "")
    if age_label not in WANT_AGES:
        continue
    measure = lfst_map.get(r.get("lfst_code", ""), "")
    if measure != WANT_MEASURE:
        continue
    if bothsex_codes and r.get("sexs_code") not in bothsex_codes:
        continue
    sid = r["series_id"].strip()
    if sid.endswith("Q"):
        continue
    title = r.get("series_title", "")
    if "Men" in title or "Women" in title:
        continue
    race_label = race_map.get(r.get("race_code", ""), r.get("race_code", ""))
    # prefer the plainest title: shortest one ending in the race label
    key = (race_label, age_label)
    cur = results.get(key)
    if cur is None or len(title) < len(cur["title"]):
        results[key] = {"series_id": sid, "title": title,
                        "seasonal": r.get("seasonal", "")}

# Data availability check
wanted_ids = {v["series_id"] for v in results.values()}
latest = {}
if wanted_ids:
    with open(DATA_FILE, "r", encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            sid = line.split("\t", 1)[0].strip()
            if sid in wanted_ids:
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 4:
                    y, p, v = parts[1].strip(), parts[2].strip(), parts[3].strip()
                    prev = latest.get(sid)
                    if prev is None or (int(y), p) > (int(prev[0]), prev[1]):
                        latest[sid] = (y, p, v)

print("=== Population series by race, for 25-54 and 16+ (Both Sexes) ===\n")
races_seen = sorted({k[0] for k in results})
for age in ["25 to 54 years", "16 years and over"]:
    print(f"--- {age} ---")
    for race in races_seen:
        p = results.get((race, age))
        if not p:
            print(f"  [none]  {race}")
            continue
        sid = p["series_id"]
        last = latest.get(sid)
        last_str = f"{last[0]}-{last[1]}={last[2]}" if last else "no-data"
        print(f"  {sid:<14} SA={p['seasonal']} last={last_str:<16} {race}")
        print(f"       {p['title']}")
    print()

print("Pull the 25-54 series for each non-White group that GREW, plus White (LNU00000063),")
print("then compare the Jan-2026 code-12 steps. Do the non-White prime-age GAINS")
print("sum to ~+3,984 (a clean transfer) or much less (not a clean transfer)?")

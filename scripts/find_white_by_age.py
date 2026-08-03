#!/usr/bin/env python3
"""
Find White-by-age CPS (LN) series in the local flat-file catalog, and confirm
which ones actually have data in ln.data.1.AllData.txt.

Why this exists: LN series IDs are NOT decodable by eye. Rather than guess,
we read the catalog (ln.series) + the mapping files (ln.race, ln.ages,
ln.lfst / measure files), join codes to labels, filter to White + an age band,
then check the data file for a recent (2026) observation so we know the series
is populated, not just catalogued.

Usage:
    python3 scripts/find_white_by_age.py                 # dumps all White x age x measure
    python3 scripts/find_white_by_age.py participation    # filter measures containing "participation"
    python3 scripts/find_white_by_age.py "not in labor"   # filter measures containing that text

Reads the flat files from <repo>/data, resolved relative to this script,
so it runs from any working directory.

NOTE: this script makes NO assumptions about exact column names beyond the
standard BLS layout. It prints the catalog's own column header first so we can
see what's there. If a mapping filename differs on your machine, it will say so
and list what it DID find, so we can adjust.
"""

import os
import sys
import glob

LN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      os.pardir, "data")
SERIES_FILE = os.path.join(LN_DIR, "ln.series")
DATA_FILE = os.path.join(LN_DIR, "ln.data.1.AllData.txt")

measure_filter = sys.argv[1].strip().lower() if len(sys.argv) > 1 else ""


def die(msg):
    sys.exit(msg)


if not os.path.exists(SERIES_FILE):
    # try a .txt variant, since AllData had one
    alt = SERIES_FILE + ".txt"
    if os.path.exists(alt):
        SERIES_FILE = alt
    else:
        die(f"Cannot find {SERIES_FILE} (or .txt). Files present in {LN_DIR}:\n" +
            "\n".join("  " + os.path.basename(p) for p in glob.glob(os.path.join(LN_DIR, "ln.*"))))

if not os.path.exists(DATA_FILE):
    die(f"Cannot find {DATA_FILE}. Expected the BLS flat files in <repo>/data.")


def load_tsv(path):
    """Load a tab-delimited BLS file into (header_list, list_of_dicts).
    Strips whitespace from every field and the header names."""
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = [h.strip() for h in f.readline().rstrip("\n").split("\t")]
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < len(header):
                parts += [""] * (len(header) - len(parts))
            row = {header[i]: parts[i].strip() for i in range(len(header))}
            rows.append(row)
    return header, rows


# ---- 1. Load the series catalog -------------------------------------------
series_header, series_rows = load_tsv(SERIES_FILE)
print("=== ln.series columns ===")
print(series_header)
print(f"(total catalogued series: {len(series_rows)})\n")


# ---- 2. Load mapping files we care about, if present ----------------------
def load_map(basename, code_col_hint=None):
    """Load a mapping file like ln.race or ln.ages -> {code: label}.
    BLS mapping files are typically: <char>_code \t <char>_text \t ...
    We take the first column as code and the first column containing 'text'
    (or the 2nd column) as label."""
    path = os.path.join(LN_DIR, basename)
    if not os.path.exists(path):
        path_txt = path + ".txt"
        if os.path.exists(path_txt):
            path = path_txt
        else:
            return None, None, None
    hdr, rows = load_tsv(path)
    code_col = hdr[0]
    # find a label column
    label_col = None
    for h in hdr:
        if h != code_col and "text" in h.lower():
            label_col = h
            break
    if label_col is None and len(hdr) >= 2:
        label_col = hdr[1]
    mapping = {r[code_col]: r.get(label_col, "") for r in rows}
    return code_col, label_col, mapping


race_code_col, race_label_col, race_map = load_map("ln.race")
age_code_col, age_label_col, age_map = load_map("ln.ages")
# measure text can live in a few files; try common ones
lfst_code_col, lfst_label_col, lfst_map = load_map("ln.lfst")

print("=== mapping files loaded ===")
print(f"race:  {'ok' if race_map else 'MISSING'} "
      f"(code col: {race_code_col}, label col: {race_label_col}, n={len(race_map) if race_map else 0})")
print(f"ages:  {'ok' if age_map else 'MISSING'} "
      f"(code col: {age_code_col}, label col: {age_label_col}, n={len(age_map) if age_map else 0})")
print(f"lfst:  {'ok' if lfst_map else 'MISSING'} "
      f"(code col: {lfst_code_col}, label col: {lfst_label_col}, n={len(lfst_map) if lfst_map else 0})")
print()

if not race_map or not age_map:
    print("WARNING: race or ages mapping missing. Listing all ln.* files so we can adjust:")
    for p in sorted(glob.glob(os.path.join(LN_DIR, "ln.*"))):
        print("   ", os.path.basename(p))
    print()

# Identify which race code(s) mean White
white_race_codes = set()
if race_map:
    for code, label in race_map.items():
        if label.strip().lower() == "white":
            white_race_codes.add(code)
print(f"White race code(s): {sorted(white_race_codes) or 'NOT FOUND - check ln.race labels above'}\n")


# ---- 3. Which series-catalog columns hold race / age / measure codes? ------
# Series files use short code column names like 'race_code', 'ages_code',
# 'lfst_code'. Detect them flexibly.
def find_col(header, *needles):
    for h in header:
        hl = h.lower()
        if all(n in hl for n in needles):
            return h
    return None

race_col = find_col(series_header, "race")
age_col = find_col(series_header, "age")
lfst_col = find_col(series_header, "lfst")
seasonal_col = find_col(series_header, "seasonal")
title_col = find_col(series_header, "series", "title") or find_col(series_header, "title")

print("=== detected series-catalog code columns ===")
print(f"race col: {race_col}, age col: {age_col}, lfst col: {lfst_col}, "
      f"seasonal col: {seasonal_col}, title col: {title_col}\n")

if not (race_col and age_col):
    die("Could not detect race/age code columns in ln.series. "
        "Look at the 'ln.series columns' printout above and tell me the names.")


# ---- 4. Filter catalog to White x (any age) x (measure filter) -------------
matches = []
for r in series_rows:
    if white_race_codes and r.get(race_col) not in white_race_codes:
        continue
    age_label = age_map.get(r.get(age_col, ""), "") if age_map else ""
    lfst_label = lfst_map.get(r.get(lfst_col, ""), "") if (lfst_map and lfst_col) else ""
    title = r.get(title_col, "") if title_col else ""
    # measure filter matches against lfst label OR the human title
    haystack = (lfst_label + " " + title).lower()
    if measure_filter and measure_filter not in haystack:
        continue
    matches.append({
        "series_id": r[series_header[0]],
        "age": age_label,
        "measure": lfst_label,
        "seasonal": r.get(seasonal_col, "") if seasonal_col else "",
        "title": title,
    })

print(f"=== {len(matches)} White series match "
      f"(measure filter: {measure_filter!r}) ===\n")


# ---- 5. Confirm data availability: does each series have a 2026 row? --------
wanted_ids = {m["series_id"].strip() for m in matches}
latest = {}  # series_id -> (year, period, value)
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

# ---- 6. Print the result table --------------------------------------------
def sort_key(m):
    return (m["measure"], m["age"], m["seasonal"])

for m in sorted(matches, key=sort_key):
    sid = m["series_id"].strip()
    last = latest.get(sid)
    has_data = "DATA" if last else "no-data"
    last_str = f"{last[0]}-{last[1]}={last[2]}" if last else "-"
    print(f"{sid:<16} [{has_data:<7}] last={last_str:<16} "
          f"| age={m['age']!r} | measure={m['measure']!r} | SA={m['seasonal']!r}")
    if m["title"]:
        print(f"{'':<16} title: {m['title']}")

print(f"\nDone. {sum(1 for s in latest if latest[s])} of {len(matches)} "
      f"matched series have data in AllData.")

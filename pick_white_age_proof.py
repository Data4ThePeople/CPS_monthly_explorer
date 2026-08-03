#!/usr/bin/env python3
"""
Narrow the White-by-age catalog to the FEW series needed to test whether the
Jan-2026 White participation drop is an age-composition (mix) effect.

We want, for White, Both Sexes, these age bands: 16+ (overall), 25-54 (prime),
55+ , 65+ . And two measures: 'Civilian labor force participation rate' and
'Civilian noninstitutional population'. Seasonally adjusted preferred (SA='S'),
falling back to unadjusted (SA='U') when SA isn't published for a cut.

We exclude Men/Women-specific and enrolled-in-school / veteran / etc. variants
by requiring the title to be the plain "..., White" form (no extra qualifier
after White, no 'Men'/'Women').

Usage:
    python3 pick_white_age_proof.py

Prints a short list of verified series_ids to feed into check_series_tail.py.
"""

import os
import re
import glob

LN_DIR = os.path.expanduser("~/Desktop/ln")
SERIES_FILE = os.path.join(LN_DIR, "ln.series")
DATA_FILE = os.path.join(LN_DIR, "ln.data.1.AllData.txt")

for cand in (SERIES_FILE, SERIES_FILE + ".txt"):
    if os.path.exists(cand):
        SERIES_FILE = cand
        break

# Age bands we care about (exact ages_text labels as seen in the dump)
WANT_AGES = {
    "16 years and over",
    "25 to 54 years",
    "55 years and over",
    "65 years and over",
}
WANT_MEASURES = {
    "Civilian labor force participation rate",
    "Civilian noninstitutional population",
}


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
    label_col = next((k for k in keys if "text" in k.lower()), keys[1] if len(keys) > 1 else keys[0])
    return {r[code_col]: r[label_col] for r in rows}


race_map = load_map("ln.race")
age_map = load_map("ln.ages")
lfst_map = load_map("ln.lfst")
sexs_map = load_map("ln.sexs")

white_codes = {c for c, l in race_map.items() if l.strip().lower() == "white"}
# Both Sexes code
bothsex_codes = {c for c, l in sexs_map.items() if l.strip().lower() in ("both sexes", "both")}

picks = []
for r in load_tsv(SERIES_FILE):
    if r.get("race_code") not in white_codes:
        continue
    # Both Sexes only (if sexs mapping available)
    if bothsex_codes and r.get("sexs_code") not in bothsex_codes:
        continue
    age_label = age_map.get(r.get("ages_code", ""), "")
    if age_label not in WANT_AGES:
        continue
    measure = lfst_map.get(r.get("lfst_code", ""), "")
    if measure not in WANT_MEASURES:
        continue
    sid = r["series_id"].strip()
    if sid.endswith("Q"):  # skip quarterly
        continue
    title = r.get("series_title", "")
    # require plain "White" form: ends with ", White" and no Men/Women
    if "Men" in title or "Women" in title:
        continue
    if not re.search(r",\s*White\b", title):
        continue
    picks.append({
        "series_id": sid,
        "age": age_label,
        "measure": measure,
        "seasonal": r.get("seasonal", ""),
        "title": title,
        "begin": f"{r.get('begin_year','')}-{r.get('begin_period','')}",
    })

# Prefer SA over U when both exist for same (age, measure)
best = {}
for p in picks:
    key = (p["age"], p["measure"])
    cur = best.get(key)
    if cur is None or (p["seasonal"] == "S" and cur["seasonal"] != "S"):
        best[key] = p

order_age = ["16 years and over", "25 to 54 years", "55 years and over", "65 years and over"]
order_meas = ["Civilian labor force participation rate", "Civilian noninstitutional population"]

print("=== Series to pull for the White age-composition proof ===\n")
for meas in order_meas:
    print(f"--- {meas} ---")
    for age in order_age:
        p = best.get((age, meas))
        if p:
            print(f"  {p['series_id']:<14} SA={p['seasonal']}  age={p['age']:<20} "
                  f"(from {p['begin']})")
            print(f"       {p['title']}")
        else:
            print(f"  [none found]   age={age:<20} {meas}")
    print()

print("Feed the IDs above into:  python3 check_series_tail.py <id> 18")

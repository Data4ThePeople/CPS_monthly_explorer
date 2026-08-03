#!/usr/bin/env bash
# Download + unzip CPS basic monthly public-use CSVs.
#   ./fetch_cps.sh 2023 2026
# Files land in <repo>/data/cps/ as e.g. jun26pub.csv, regardless of where you
# run this from.
#
# Landing page (has the per-month links and the Data Dictionary_CSV):
#   https://www.census.gov/data/datasets/time-series/demo/cps/cps-basic.html
#
# No oct25 file exists (appropriations lapse, no collection). The skip is correct.
# Two jan26 files exist; this fetches the corrected re-release. The original is at
#   census.gov/programs-surveys/cps/data/cps-dataset-revision-archive.html

set -euo pipefail
START=${1:?usage: fetch_cps.sh START_YEAR END_YEAR}
END=${2:?usage: fetch_cps.sh START_YEAR END_YEAR}
BASE="https://www2.census.gov/programs-surveys/cps/datasets"
MONTHS=(jan feb mar apr may jun jul aug sep oct nov dec)

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$REPO_ROOT/data/cps" && cd "$REPO_ROOT/data/cps"
for y in $(seq "$START" "$END"); do
  yy=$(printf "%02d" $((y % 100)))
  for m in "${MONTHS[@]}"; do
    [[ -f "${m}${yy}pub.csv" ]] && { echo "have ${m}${yy}pub.csv"; continue; }
    z="${m}${yy}pub.zip"
    if curl -fsSL -o "$z" "${BASE}/${y}/basic/${z}"; then
      unzip -oq "$z" && rm -f "$z"
      echo "ok   ${m}${yy}pub.csv"
    else
      echo "skip ${z} (not published, or 404)"
    fi
  done
done

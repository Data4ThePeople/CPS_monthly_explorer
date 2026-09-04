#!/usr/bin/env bash
#
# refresh.sh -- rebuild the LN explorer against a new BLS monthly release.
#
# Run this on release morning. It does, in order:
#
#   1. Probes the API for the bellwether series and compares it against what
#      is already cached. If BLS has not published a newer month yet, it stops
#      instead of burning a full refresh on data you already have.
#   2. Downloads a fresh ln.series catalog (new/discontinued series, updated
#      end dates).
#   3. Rebuilds the explorer with --refresh, then regenerates the page
#      schema (v2/output/schema*.jsonld) from the rebuilt explorer. The
#      schema is committed alongside the explorer but never pushed anywhere
#      else -- paste it into the CMS by hand.
#
# --refresh is not optional and is the reason this script exists. bls_client
# treats a cached series as fresh while it holds data through today-minus-two
# months, so on release morning the cache still looks current and a plain
# rebuild would silently reproduce last month's numbers with no error.
#
# Usage:
#   ./v2/refresh.sh              build only, then print what to do next
#   ./v2/refresh.sh --publish    also commit, push, deploy Pages, verify live
#   ./v2/refresh.sh --force      rebuild even if no new month was found
#
# Cost: ~176 API queries of the registered 500/day. Do not run repeatedly.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$REPO/.venv/bin/python"
CATALOG="$REPO/data/ln.series.txt"
CATALOG_URL="https://download.bls.gov/pub/time.series/ln/ln.series"
BUILT="$REPO/v2/output/ln_explorer.html"
SCHEMA="$REPO/v2/output/schema.jsonld"
SCHEMA_INTRO="$REPO/v2/output/schema-intro.jsonld"
LIVE="https://data4thepeople.github.io/CPS_monthly_explorer/v2/output/ln_explorer.html"
GH_REPO="Data4ThePeople/CPS_monthly_explorer"
BELLWETHER="LNS12000000"          # Employment Level, seasonally adjusted
UA="CPS_monthly_explorer (eric@asaltollc.com)"

PUBLISH=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --publish) PUBLISH=1 ;;
    --force)   FORCE=1 ;;
    -h|--help) sed -n '2,28p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

[ -x "$PY" ] || die "no interpreter at $PY -- create the venv and pip install -r requirements.txt"
[ -f "$REPO/.env" ] || die "no .env at $REPO/.env -- BLS_API_KEY is required"

cd "$REPO"

# --------------------------------------------------------------------------
say "1/4  Checking whether BLS has published a new month"

# Latest month already cached, then latest month the API will serve right now.
# Uses only bls_client's public fetch(); the second call costs ~4 queries.
BEFORE="$("$PY" - <<'PY'
import sys, contextlib, io
sys.path.insert(0, "v2")
import bls_client
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        df = bls_client.fetch(["LNS12000000"])
    print(df["date"].max().strftime("%Y-%m"))
except SystemExit:
    print("none")
PY
)"

AFTER="$("$PY" - <<'PY'
import sys, contextlib, io
sys.path.insert(0, "v2")
import bls_client
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    df = bls_client.fetch(["LNS12000000"], refresh=True)
print(df["date"].max().strftime("%Y-%m"))
PY
)"

echo "  cached through : $BEFORE"
echo "  API serves through: $AFTER   ($BELLWETHER)"

if [ "$AFTER" = "$BEFORE" ] && [ "$FORCE" -eq 0 ]; then
  cat <<EOF

No new month yet -- the API still ends at $AFTER, same as your last build.
BLS often posts the API a little after the 8:30am press release. Wait and
rerun, or use --force to rebuild anyway.

Nothing was changed. No full refresh was spent.
EOF
  exit 0
fi
[ "$AFTER" = "$BEFORE" ] && echo "  --force given: rebuilding despite no new month"

# --------------------------------------------------------------------------
say "2/4  Downloading fresh series catalog"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
curl -fsS -A "$UA" -o "$TMP" "$CATALOG_URL" || die "catalog download failed"
# Only replace the real file once the download succeeded and looks sane, so a
# truncated response can never leave you without a usable catalog.
LINES="$(wc -l < "$TMP" | tr -d ' ')"
[ "$LINES" -gt 50000 ] || die "catalog looks truncated ($LINES lines) -- keeping the existing one"
head -1 "$TMP" | grep -q "series_id" || die "catalog missing its header row -- keeping the existing one"
mv "$TMP" "$CATALOG"
trap - EXIT
echo "  $CATALOG  ($LINES lines, $(du -h "$CATALOG" | cut -f1))"

# --------------------------------------------------------------------------
say "3/4  Rebuilding the explorer (full refresh, ~176 queries)"
"$PY" v2/build_explorer.py --refresh

# Confirm the built file really contains the new month before anyone ships it.
BUILT_THROUGH="$("$PY" - <<'PY'
import re, json, pathlib
h = pathlib.Path("v2/output/ln_explorer.html").read_text(encoding="utf-8", errors="replace")
db = json.loads(re.search(r'(?:const|var|let)\s+DB\s*=\s*(\{.*?\});\s*\n', h, re.S).group(1))
hi = max(divmod(s["y0"]*12 + (s["m0"]-1) + len(s["v"]) - 1, 12) for s in db["series"].values())
print(f"{hi[0]}-{hi[1]+1:02d}")
PY
)"
echo
echo "  built file runs through: $BUILT_THROUGH"
[ "$BUILT_THROUGH" = "$AFTER" ] || die "built file ends at $BUILT_THROUGH but the API served $AFTER -- do not publish this"

# The schema is derived from the built explorer (measure list, breakdowns,
# counts), so it is regenerated after every rebuild. Only after the build has
# been verified above -- never from a stale explorer.
echo
echo "  regenerating page schema ..."
"$PY" v2/build_schema.py | sed 's/^/  /'

# --------------------------------------------------------------------------
if [ "$PUBLISH" -eq 0 ]; then
  say "4/4  Done (not published)"
  cat <<EOF
The rebuilt explorer is at:
  $BUILT

To publish it:
  ./v2/refresh.sh --publish     (reruns the whole thing), or by hand:
  git add v2/output/ln_explorer.html v2/output/schema.jsonld v2/output/schema-intro.jsonld
  git commit -m "Rebuild explorer with $BUILT_THROUGH data"
  git push
  gh api -X POST repos/$GH_REPO/pages/builds

The schema files are not pushed anywhere else -- copy and paste them into the
CMS by hand:
  $SCHEMA
  $SCHEMA_INTRO
EOF
  exit 0
fi

say "4/4  Publishing"
if git diff --quiet -- "$BUILT" "$SCHEMA" "$SCHEMA_INTRO"; then
  echo "  explorer HTML and schema are unchanged -- nothing to commit"
else
  git add "$BUILT" "$SCHEMA" "$SCHEMA_INTRO"
  git commit -q -m "Rebuild explorer with $BUILT_THROUGH data"
  git push -q origin main
  echo "  pushed $(git rev-parse --short HEAD)"
fi

# Push-triggered Pages builds on this repo hang; a manual build completes in
# well under a minute. Always trigger explicitly.
echo "  triggering Pages build ..."
gh api -X POST "repos/$GH_REPO/pages/builds" >/dev/null
for i in $(seq 1 20); do
  status="$(gh api "repos/$GH_REPO/pages/builds/latest" --jq .status 2>/dev/null || echo unknown)"
  if [ "$status" = "built" ]; then echo "  build $status"; break; fi
  if [ "$status" = "errored" ]; then
    gh api "repos/$GH_REPO/pages/builds/latest" --jq '.error.message' >&2
    die "Pages build failed"
  fi
  sleep 10
done

echo "  verifying live file ..."
for i in $(seq 1 20); do
  if curl -fsS -o "$TMP.live" "$LIVE" 2>/dev/null && cmp -s "$TMP.live" "$BUILT"; then
    rm -f "$TMP.live"
    say "Live and verified: $LIVE"
    echo "Serving $BUILT_THROUGH data, byte-identical to the local build."
    echo
    echo "Schema regenerated and committed, not pushed to the CMS -- paste by hand:"
    echo "  $SCHEMA"
    echo "  $SCHEMA_INTRO"
    exit 0
  fi
  sleep 15
done
rm -f "$TMP.live" 2>/dev/null || true
die "deployed file did not match the local build within ~5 min (Pages caches for 10 min; recheck shortly)"

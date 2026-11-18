#!/bin/bash
# usage: lighthouse_runs.sh URL OUTDIR [MOBILE_RUNS] [DESKTOP_RUNS]
#   -> OUTDIR/lh-mobile-N.json, OUTDIR/lh-desktop-N.json (sequential runs; default 3 + 3,
#      subpages use 1 0 = one mobile run)
set -u
LH_VERSION="13.6.0"
URL="$1"; OUT="$2"; MOBILE_RUNS="${3:-3}"; DESKTOP_RUNS="${4:-3}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
CHROME_PATH="$(bash "$HERE/chrome.sh" --print-path)" || { echo "site-review: brak Chrome — pomijam Lighthouse" >&2; exit 3; }
export CHROME_PATH
ok=0
for FORM in mobile desktop; do
  PRESET=""; RUNS="$MOBILE_RUNS"
  [ "$FORM" = desktop ] && PRESET="--preset=desktop" && RUNS="$DESKTOP_RUNS"
  for ((i = 1; i <= RUNS; i++)); do
    if npx -y "lighthouse@$LH_VERSION" "$URL" --output=json --output-path="$OUT/lh-$FORM-$i.json" --quiet \
         --chrome-flags="--headless=new --no-first-run" $PRESET \
         --only-categories=performance,accessibility,seo,best-practices >/dev/null 2>&1; then
      ok=$((ok+1))
    else
      echo "site-review: przebieg Lighthouse $FORM #$i nieudany" >&2
    fi
  done
done
echo "site-review: udane przebiegi Lighthouse: $ok/$((MOBILE_RUNS + DESKTOP_RUNS))"
[ "$ok" -gt 0 ]

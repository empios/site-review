#!/bin/bash
# usage: lighthouse_runs.sh URL OUTDIR  -> OUTDIR/lh-{mobile,desktop}-{1,2,3}.json (sequential runs)
set -u
LH_VERSION="13.6.0"
URL="$1"; OUT="$2"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
CHROME_PATH="$(bash "$HERE/chrome.sh" --print-path)" || { echo "site-review: brak Chrome — pomijam Lighthouse" >&2; exit 3; }
export CHROME_PATH
ok=0
for FORM in mobile desktop; do
  PRESET=""
  [ "$FORM" = desktop ] && PRESET="--preset=desktop"
  for i in 1 2 3; do
    if npx -y "lighthouse@$LH_VERSION" "$URL" --output=json --output-path="$OUT/lh-$FORM-$i.json" --quiet \
         --chrome-flags="--headless=new --no-first-run" $PRESET \
         --only-categories=performance,accessibility,seo,best-practices >/dev/null 2>&1; then
      ok=$((ok+1))
    else
      echo "site-review: przebieg Lighthouse $FORM #$i nieudany" >&2
    fi
  done
done
echo "site-review: udane przebiegi Lighthouse: $ok/6"
[ "$ok" -gt 0 ]

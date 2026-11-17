#!/bin/bash
# usage: screenshots.sh URL OUTDIR  -> OUTDIR/shot-375.png, shot-768.png, shot-1440.png
set -u
URL="$1"; OUT="$2"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
status=0
for W in 375 768 1440; do
  bash "$HERE/chrome.sh" --headless=new --disable-gpu --hide-scrollbars --virtual-time-budget=8000 \
    --window-size="$W,2000" --screenshot="$OUT/shot-$W.png" "$URL" >/dev/null || status=$?
  [ -s "$OUT/shot-$W.png" ] || { echo "site-review: brak zrzutu $W px" >&2; status=1; }
done
exit $status

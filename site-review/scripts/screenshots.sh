#!/bin/bash
# usage: screenshots.sh URL OUTDIR
#   -> OUTDIR/shot-375.png, shot-768.png, shot-1440.png, shot-375-dark.png, metrics.json
# Real device emulation through the DevTools Protocol (window-size alone cannot go below ~500 px).
# Exit 3 = no Chrome or no Node 22+; exit 1 = page/screenshot failure.
set -u
URL="$1"; OUT="$2"
HERE="$(cd "$(dirname "$0")" && pwd)"
CHROME="$(bash "$HERE/chrome.sh" --print-path)" || exit 3
command -v node >/dev/null 2>&1 || { echo "site-review: brak Node (wymagany 22+)" >&2; exit 3; }
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
[ "$NODE_MAJOR" -ge 22 ] || { echo "site-review: Node $NODE_MAJOR < 22 (brak wbudowanego WebSocket)" >&2; exit 3; }
mkdir -p "$OUT"
node "$HERE/screenshot.mjs" "$CHROME" "$URL" "$OUT"

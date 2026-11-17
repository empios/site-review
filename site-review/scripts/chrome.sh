#!/bin/bash
# Run Chrome/Chromium with the given arguments. Exit 3 when no browser is found.
set -u
find_chrome() {
  if [ -n "${CHROME_PATH:-}" ] && [ -x "$CHROME_PATH" ]; then echo "$CHROME_PATH"; return; fi
  local mac="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  if [ -x "$mac" ]; then echo "$mac"; return; fi
  for c in google-chrome google-chrome-stable chromium chromium-browser; do
    if command -v "$c" >/dev/null 2>&1; then command -v "$c"; return; fi
  done
}
CHROME="$(find_chrome)"
if [ -z "$CHROME" ]; then
  echo "site-review: nie znaleziono Chrome/Chromium (ustaw CHROME_PATH)" >&2
  exit 3
fi
if [ "${1:-}" = "--print-path" ]; then echo "$CHROME"; exit 0; fi
exec "$CHROME" --no-first-run --no-default-browser-check --user-data-dir="$(mktemp -d)" "$@" 2>/dev/null

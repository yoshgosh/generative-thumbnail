#!/usr/bin/env bash
set -euo pipefail

TARGET="src/assets/fonts/NotoSansJP-Bold.ttf"
TARGET_DIR="$(dirname "$TARGET")"

find_default_source() {
  local candidates=(
    "/Library/Fonts/Noto Sans JP/static/NotoSansJP-Bold.ttf"
    "/System/Library/Fonts/NotoSansJP-Bold.otf"
    "/Library/Fonts/NotoSansJP-Bold.otf"
    "/usr/local/share/fonts/NotoSansJP-Bold.otf"
  )
  for path in "${candidates[@]}"; do
    if [[ -f "$path" ]]; then
      printf "%s" "$path"
      return 0
    fi
  done
  return 1
}

SOURCE="${1:-}"
if [[ -z "$SOURCE" ]]; then
  if ! SOURCE="$(find_default_source)"; then
    echo "Font source not found."
    echo "Usage: ./scripts/install_font.sh /path/to/NotoSansJP-Bold.ttf"
    exit 1
  fi
fi

if [[ ! -f "$SOURCE" ]]; then
  echo "Font file does not exist: $SOURCE"
  exit 1
fi

mkdir -p "$TARGET_DIR"
cp "$SOURCE" "$TARGET"
echo "Installed bundled font:"
echo "  source: $SOURCE"
echo "  target: $TARGET"

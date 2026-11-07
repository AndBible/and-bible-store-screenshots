#!/usr/bin/env bash
# Copies the caption fonts listed in fonts.yaml from the system font directories into ./fonts/
# (gitignored, never committed: the CJK collection is ~20 MB). Debian/Ubuntu packages:
#   sudo apt install fonts-noto-core fonts-noto-cjk
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p fonts
status=0
while read -r file dir; do
  src="/usr/share/fonts/$dir/$file"
  if [ -f "$src" ]; then
    cp -u "$src" "fonts/$file"
  else
    echo "fetch-fonts: missing $src (install fonts-noto-core / fonts-noto-cjk)" >&2
    status=1
  fi
done < <(sed -nE 's/.*file: ([^,]+),.*dir: ([^,]+),.*/\1 \2/p' fonts.yaml | sort -u)
for pkg in fonts-noto-core fonts-noto-cjk; do
  [ -f "/usr/share/doc/$pkg/copyright" ] && cp -u "/usr/share/doc/$pkg/copyright" "fonts/copyright-$pkg"
done
cat > fonts/OFL.txt <<'T'
The Noto fonts in this folder are copyright The Noto Project Authors and are licensed under the
SIL Open Font License, Version 1.1 (https://openfontlicense.org). They were copied unmodified
from the system fonts installed by the Debian packages fonts-noto-core and fonts-noto-cjk; the
full licence text and copyright holders are in the copyright-<package> files next to this one.
This folder is not committed to the repository (see ../.gitignore); run ../style/fetch-fonts.sh.
T
exit $status

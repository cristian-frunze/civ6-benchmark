#!/usr/bin/env bash
# zget <remote windows path> <local file>: fetch a file from the Zenbook over SSH
set -euo pipefail
ps="[Convert]::ToBase64String([IO.File]::ReadAllBytes('$1'))"
enc=$(printf '%s' "$ps" | iconv -f utf-8 -t utf-16le | base64 -w0)
ssh -o BatchMode=yes "${CIV_HOST:-zenbook}" "powershell -NoProfile -NonInteractive -OutputFormat Text -EncodedCommand $enc" 2>/dev/null | tr -d '\r\n ' | base64 -d > "$2"
ls -la "$2"

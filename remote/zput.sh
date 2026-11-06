#!/usr/bin/env bash
# zput <local file> <remote windows path>: copy a file to the Zenbook over SSH (scp is closed there).
# Sent in 4 KB base64 chunks, each inside its own command: a Windows command line holds ~32K characters, and
# stdin piped to PowerShell over Windows OpenSSH hangs past ~8 KB.
set -euo pipefail
dest="$2"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
base64 -w0 "$1" | fold -w 4000 > "$tmp/chunks"
[ -s "$tmp/chunks" ] || echo "" > "$tmp/chunks"
first=1
while IFS= read -r chunk || [ -n "$chunk" ]; do
  if [ $first = 1 ]; then mode="Create"; first=0; else mode="Append"; fi
  ps="\$p='$dest'; New-Item -ItemType Directory -Force -Path (Split-Path \$p) | Out-Null; \$b=[Convert]::FromBase64String('$chunk'); \$f=[IO.File]::Open(\$p + '.part', '$mode'); \$f.Write(\$b, 0, \$b.Length); \$f.Close()"
  enc=$(printf '%s' "$ps" | iconv -f utf-8 -t utf-16le | base64 -w0)
  ssh -o BatchMode=yes "${CIV_HOST:-zenbook}" "powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand $enc" >/dev/null 2>&1 < /dev/null
done < "$tmp/chunks"
ps="\$p='$dest'; Move-Item -Force (\$p + '.part') \$p; 'wrote ' + \$p + ' ' + (Get-Item \$p).Length"
enc=$(printf '%s' "$ps" | iconv -f utf-8 -t utf-16le | base64 -w0)
ssh -o BatchMode=yes "${CIV_HOST:-zenbook}" "powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand $enc" 2>/dev/null < /dev/null | sed 's/<Objs.*<\/Objs>//' | grep -v '^#< CLIXML'

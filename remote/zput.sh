#!/usr/bin/env bash
# zput <local file> <remote windows path>: copy a small file to the Zenbook over SSH (scp is closed there)
set -euo pipefail
b=$(base64 -w0 "$1")
ps="\$p='$2'; New-Item -ItemType Directory -Force -Path (Split-Path \$p) | Out-Null; [IO.File]::WriteAllBytes(\$p, [Convert]::FromBase64String('$b')); 'wrote ' + \$p + ' ' + (Get-Item \$p).Length"
enc=$(printf '%s' "$ps" | iconv -f utf-8 -t utf-16le | base64 -w0)
ssh -o BatchMode=yes "${CIV_HOST:-zenbook}" "powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand $enc" 2>/dev/null | sed 's/<Objs.*<\/Objs>//' | grep -v '^#< CLIXML'

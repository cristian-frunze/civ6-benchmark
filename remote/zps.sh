#!/usr/bin/env bash
# zps <ps1 file> | zps -c '<powershell>': run PowerShell on the Windows game PC (CIV_HOST, default zenbook); prints stdout, then any errors
set -euo pipefail
if [ "$1" = "-c" ]; then src="$2"; else src=$(cat "$1"); fi
wrapped="\$ProgressPreference='SilentlyContinue'; \$Error.Clear(); & { $src } 2>&1 | Out-String -Width 300; if (\$Error.Count) { 'ERRORS:'; \$Error | ForEach-Object { '  ' + \$_.ToString() } }"
enc=$(printf '%s' "$wrapped" | iconv -f utf-8 -t utf-16le | base64 -w0)
ssh -o BatchMode=yes "${CIV_HOST:-zenbook}" "powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -OutputFormat Text -EncodedCommand $enc" 2>/dev/null

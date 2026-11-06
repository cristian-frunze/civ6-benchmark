#!/usr/bin/env bash
# zexec <local .ps1> [timeout seconds]: run a PowerShell file inside the game PC's desktop session, where windows,
# screens and input exist (SSH runs in session 0, which has none). Goes through the Civ6Exec scheduled task.
set -euo pipefail
b=$(base64 -w0 "$1"); t=${2:-60}
ps="\$ProgressPreference='SilentlyContinue'; \$d=Join-Path \$env:USERPROFILE 'civ6-bench\exec'; New-Item -ItemType Directory -Force -Path \$d | Out-Null
Remove-Item (Join-Path \$d 'job.out'),(Join-Path \$d 'job.done') -ErrorAction SilentlyContinue
[IO.File]::WriteAllBytes((Join-Path \$d 'job.ps1'), [Convert]::FromBase64String('$b'))
Start-ScheduledTask -TaskName Civ6Exec
\$i=0; while (-not (Test-Path (Join-Path \$d 'job.done')) -and \$i -lt ($t*4)) { Start-Sleep -Milliseconds 250; \$i++ }
if (Test-Path (Join-Path \$d 'job.done')) { Get-Content (Join-Path \$d 'job.out') -Raw } else { 'TIMEOUT waiting for the desktop job' }"
enc=$(printf '%s' "$ps" | iconv -f utf-8 -t utf-16le | base64 -w0)
ssh -o BatchMode=yes "${CIV_HOST:-zenbook}" "powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -OutputFormat Text -EncodedCommand $enc" 2>/dev/null

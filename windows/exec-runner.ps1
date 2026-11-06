# Runs %USERPROFILE%\civ6-bench\exec\job.ps1 inside the signed-in user's desktop session (via the Civ6Exec
# scheduled task) and writes its output to job.out, then job.done. remote/zexec.sh uploads the job and waits.
$d = Join-Path $env:USERPROFILE 'civ6-bench\exec'
$out = Join-Path $d 'job.out'; $done = Join-Path $d 'job.done'
try { & (Join-Path $d 'job.ps1') *>&1 | Out-String -Width 300 | Set-Content $out -Encoding UTF8 }
catch { "ERROR: $_" | Add-Content $out -Encoding UTF8 }
Set-Content $done (Get-Date -Format o)

# Open the war room page full screen on the second (non-primary) screen, in its own Chrome app window and profile.
# Reads %USERPROFILE%\civ6-bench\warroom.json: {"url": "https://<host>/share/civ6-warroom/", "ip": "<host's tailnet IP>"}
# The IP is mapped in this browser only (--host-resolver-rules), for PCs whose Tailscale DNS is off. Kept out of the repo.
# --test-type hides the "unsupported command-line flag" bar, which would otherwise print the IP on screen.
# Run in the desktop session (remote/zexec.sh).
$dir = Join-Path $env:USERPROFILE 'civ6-bench'
$cfg = Get-Content (Join-Path $dir 'warroom.json') -Raw | ConvertFrom-Json
$chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$prof = Join-Path $dir 'chrome-warroom'
Add-Type -AssemblyName System.Windows.Forms
$scr = [System.Windows.Forms.Screen]::AllScreens | Where-Object { -not $_.Primary } | Select-Object -First 1
if (-not $scr) { $scr = [System.Windows.Forms.Screen]::PrimaryScreen }
$b = $scr.Bounds   # logical (DPI-scaled) coordinates, which is what Chrome's window flags take
Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -like "*chrome-warroom*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 500
$hostName = ([Uri]$cfg.url).Host
$args = @("--app=$($cfg.url)", "--user-data-dir=`"$prof`"", "--no-first-run", "--no-default-browser-check", "--test-type",
  "--window-position=$($b.X),$($b.Y)", "--window-size=$($b.Width),$($b.Height)", "--start-fullscreen")
if ($cfg.ip) { $args += "--host-resolver-rules=`"MAP $hostName $($cfg.ip)`"" }
Start-Process -FilePath $chrome -ArgumentList $args
"opened $($cfg.url) on $($scr.DeviceName) at $($b.X),$($b.Y) $($b.Width)x$($b.Height)"

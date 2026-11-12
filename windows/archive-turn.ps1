# Per-turn capture for tools/archive.py: at the start of every game turn, a screenshot of both screens (game on top,
# war room below) and copies of the civ6-mcp autosaves (0_MCP_NNNN) written since the game started.
# Runs as the Civ6Archive task in the desktop session. windows/archive-sync.ps1 starts it on every sync (a running
# copy ignores the start) and writes the request:
#   %USERPROFILE%\civ6-bench\archive\request.json  {"game": "<id>", "since": <unix time>}
# It polls civ6-mcp's heartbeat every 2 s, because turns can take under 20 s, and exits after 15 idle minutes.
# Output: %USERPROFILE%\civ6-bench\archive\<id>\shots\T0042.jpg and ...\saves\0_MCP_0042.Civ6Save
$ErrorActionPreference = 'Stop'
$bench = Join-Path $env:USERPROFILE 'civ6-bench'
$hb = Join-Path $env:USERPROFILE '.civ6-mcp\heartbeat.json'
$single = Join-Path ([Environment]::GetFolderPath('MyDocuments')) "My Games\Sid Meier's Civilization VI\Saves\Single"
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type 'using System.Runtime.InteropServices; public class DpiA { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }'
[DpiA]::SetProcessDPIAware() | Out-Null

function Save-Turn($dir, [int]$turn, $since) {
    $log = Join-Path $dir 'archive-turn.log'
    try {
        $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
        $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
        $g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
        $w = [int]($b.Width * 0.4); $h = [int]($b.Height * 0.4)
        $sm = New-Object System.Drawing.Bitmap $w, $h
        $g2 = [System.Drawing.Graphics]::FromImage($sm); $g2.InterpolationMode = 'HighQualityBicubic'; $g2.DrawImage($bmp, 0, 0, $w, $h)
        $sm.Save((Join-Path $dir ('shots\T{0:D4}.jpg' -f $turn)), [System.Drawing.Imaging.ImageFormat]::Jpeg)
        $g.Dispose(); $g2.Dispose(); $bmp.Dispose(); $sm.Dispose()
    } catch { Add-Content $log "$(Get-Date -Format s) turn $turn screenshot failed: $_" }
    try {
        $t0 = [DateTimeOffset]::FromUnixTimeSeconds([long]$since).LocalDateTime
        foreach ($f in Get-ChildItem $single -Filter '0_MCP_*.Civ6Save' -File | Where-Object { $_.LastWriteTime -ge $t0 }) {
            $dest = Join-Path $dir ('saves\' + $f.Name)
            if (-not (Test-Path $dest) -or (Get-Item $dest).LastWriteTime -lt $f.LastWriteTime) { Copy-Item $f.FullName $dest -Force }
        }
    } catch { Add-Content $log "$(Get-Date -Format s) turn $turn saves failed: $_" }
}

$last = ''; $active = Get-Date
while (((Get-Date) - $active).TotalMinutes -lt 15) {
    try {
        $req = Get-Content (Join-Path $bench 'archive\request.json') -Raw | ConvertFrom-Json   # re-read: the next game reuses this loop
        $beat = Get-Content $hb -Raw | ConvertFrom-Json
        $turn = $beat.turn
        $key = "$($req.game)/$turn"
        # Only the requested game's heartbeat counts. Game 18 started 7 minutes after game 17, while the heartbeat
        # still read game 17's last turn: its folder got a T0170 shot at once, tools/archive.py took that name as
        # its watermark, and turns 1 to 169 were never synced.
        $same = (-not $beat.run_id) -or ($beat.run_id -eq $req.game)
        if ("$turn" -match '^\d+$' -and $key -ne $last -and $same) {
            $dir = Join-Path $bench ("archive\" + $req.game)
            New-Item -ItemType Directory -Force -Path (Join-Path $dir 'shots'), (Join-Path $dir 'saves') | Out-Null
            Save-Turn $dir ([int]$turn) $req.since
            $last = $key; $active = Get-Date
        }
    } catch { }   # heartbeat or request mid-write: try again next poll
    Start-Sleep -Seconds 2
}

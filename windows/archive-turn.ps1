# Archive one game turn for tools/archive.py: a screenshot of both screens (game on top, war room below) and
# copies of the civ6-mcp autosaves (0_MCP_NNNN) written since the game started. Runs as the Civ6Archive task in
# the desktop session, started by windows/archive-sync.ps1, which writes the request:
#   %USERPROFILE%\civ6-bench\archive\request.json  {"game": "<id>", "turn": N, "since": <unix time>}
# Output: %USERPROFILE%\civ6-bench\archive\<id>\shots\T0042.jpg and ...\saves\0_MCP_0042.Civ6Save
$ErrorActionPreference = 'Stop'
$bench = Join-Path $env:USERPROFILE 'civ6-bench'
$req = Get-Content (Join-Path $bench 'archive\request.json') -Raw | ConvertFrom-Json
$dir = Join-Path $bench ("archive\" + $req.game)
New-Item -ItemType Directory -Force -Path (Join-Path $dir 'shots'), (Join-Path $dir 'saves') | Out-Null
$log = Join-Path $dir 'archive-turn.log'

try {
    Add-Type -AssemblyName System.Windows.Forms, System.Drawing
    Add-Type 'using System.Runtime.InteropServices; public class DpiA { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }'
    [DpiA]::SetProcessDPIAware() | Out-Null
    $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
    $g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
    $w = [int]($b.Width * 0.4); $h = [int]($b.Height * 0.4)
    $sm = New-Object System.Drawing.Bitmap $w, $h
    $g2 = [System.Drawing.Graphics]::FromImage($sm); $g2.InterpolationMode = 'HighQualityBicubic'; $g2.DrawImage($bmp, 0, 0, $w, $h)
    $out = Join-Path $dir ('shots\T{0:D4}.jpg' -f [int]$req.turn)
    $sm.Save($out, [System.Drawing.Imaging.ImageFormat]::Jpeg)
    $g.Dispose(); $g2.Dispose(); $bmp.Dispose(); $sm.Dispose()
} catch { Add-Content $log "$(Get-Date -Format s) turn $($req.turn) screenshot failed: $_" }

try {
    $since = [DateTimeOffset]::FromUnixTimeSeconds([long]$req.since).LocalDateTime
    $single = Join-Path ([Environment]::GetFolderPath('MyDocuments')) "My Games\Sid Meier's Civilization VI\Saves\Single"
    foreach ($f in Get-ChildItem $single -Filter '0_MCP_*.Civ6Save' -File | Where-Object { $_.LastWriteTime -ge $since }) {
        $dest = Join-Path $dir ('saves\' + $f.Name)
        if (-not (Test-Path $dest) -or (Get-Item $dest).LastWriteTime -lt $f.LastWriteTime) { Copy-Item $f.FullName $dest -Force }
    }
} catch { Add-Content $log "$(Get-Date -Format s) turn $($req.turn) saves failed: $_" }

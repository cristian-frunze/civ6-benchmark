# Incremental file sync for tools/archive.py, run over SSH (remote/zps.sh). Prints, for each file that changed,
#   F <tab> key/name <tab> size <tab> offset <tab> base64 of the bytes from offset
# and "MORE" when the byte budget ran out (the next call continues). A file whose bytes before the archive's copy
# end changed (civ6-mcp rewrites its diary when it merges reflections) is sent again from offset 0.
# The spec comes on stdin (or -Spec) as base64 JSON:
#   {"roots": [{"key": "civ6mcp", "dir": "%USERPROFILE%\\.civ6-mcp", "match": ["*_<game>_<run>*", "heartbeat.json"]},
#              {"key": "shots", "dir": "...", "match": ["*.jpg"], "after": "T0041.jpg"}],   after: skip names sorting before it
#    "have": {"civ6mcp/<name>": {"size": N, "tail": "<sha1 of the 4096 bytes before N>"}},
#    "budget": 6000000,
#    "trigger": {"game": "<id>", "turn": N}}   optional: archive this turn (screenshot and saves, windows/archive-turn.ps1)
param([string]$Spec)
$ErrorActionPreference = 'Stop'
if (-not $Spec) { $Spec = [Console]::In.ReadToEnd().Trim() }
$s = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Spec)) | ConvertFrom-Json
$budget = [long]$s.budget
$sha1 = [Security.Cryptography.SHA1]::Create()

function Read-Range([string]$path, [long]$offset, [long]$count) {
    $fs = [IO.File]::Open($path, 'Open', 'Read', 'ReadWrite,Delete')
    try {
        $fs.Seek($offset, 'Begin') | Out-Null
        $buf = New-Object byte[] $count
        $n = 0
        while ($n -lt $count) { $r = $fs.Read($buf, $n, $count - $n); if ($r -le 0) { break }; $n += $r }
        if ($n -lt $count) { [Array]::Resize([ref]$buf, $n) }
        return ,$buf
    } finally { $fs.Dispose() }
}

if ($s.trigger) {
    $bench = Join-Path $env:USERPROFILE 'civ6-bench'
    $req = Join-Path $bench 'archive\request.json'
    New-Item -ItemType Directory -Force -Path (Split-Path $req) | Out-Null
    ($s.trigger | ConvertTo-Json -Compress) | Set-Content -Path $req -Encoding UTF8
    Start-ScheduledTask -TaskName 'Civ6Archive'
}

foreach ($root in $s.roots) {
    $dir = [Environment]::ExpandEnvironmentVariables($root.dir)
    if (-not (Test-Path $dir)) { continue }
    $files = foreach ($m in $root.match) { Get-ChildItem -Path $dir -Filter $m -File -ErrorAction SilentlyContinue }
    foreach ($f in ($files | Sort-Object FullName -Unique)) {
        if ($root.after -and [string]::CompareOrdinal($f.Name, [string]$root.after) -lt 0) { continue }
        $name = "$($root.key)/$($f.Name)"
        $size = $f.Length
        $have = $s.have.PSObject.Properties[$name]
        $offset = 0
        if ($have) {
            $hs = [long]$have.Value.size
            if ($hs -eq $size) { continue }
            if ($hs -lt $size -and $hs -gt 0) {
                $start = [Math]::Max(0, $hs - 4096)
                $tail = -join ($sha1.ComputeHash((Read-Range $f.FullName $start ($hs - $start))) | ForEach-Object { $_.ToString('x2') })
                if ($tail -eq $have.Value.tail) { $offset = $hs }
            }
        }
        $count = $size - $offset
        if ($count -gt $budget) {
            if ($budget -le 0) { 'MORE'; exit 0 }
            $count = $budget
        }
        $bytes = if ($count -gt 0) { Read-Range $f.FullName $offset $count } else { [byte[]]@() }
        $budget -= $count
        "F`t$name`t$size`t$offset`t$([Convert]::ToBase64String($bytes))"
        if ($offset + $count -lt $size) { 'MORE'; exit 0 }
    }
}

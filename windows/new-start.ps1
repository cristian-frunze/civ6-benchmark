# Make a new single-player game from scratch, for a new kept start (run on the game PC through remote/zexec.sh,
# between games: it stops the civ6-mcp server and kills the running game).
#   1. stops the Civ6Mcp server, which holds the only FireTuner connection
#   2. kills Civ 6 and starts it again through the Civ6Launch task
#   3. accepts the copyright screen and runs lua/new-game.lua in the MainMenu state with the settings below
#   4. waits until the map has loaded (the leader screen with BEGIN GAME is then up)
# After it: click BEGIN GAME, keep the turn-1 autosave with windows/keep-start.ps1, start the Civ6Mcp task again.
# Settings (prepend lines like these, as zexec runs one file):
#   $Speed = 'GAMESPEED_ONLINE'; $Seed = 20261106
if (-not $Speed) { $Speed = 'GAMESPEED_QUICK' }
if (-not $Seed) { $Seed = 20261106 }
$ErrorActionPreference = 'Continue'
$bench = Join-Path $env:USERPROFILE 'civ6-bench'
$mcp = Join-Path $bench 'civ6-mcp'
$lua = Join-Path $bench 'lua'
$log = Join-Path $env:LOCALAPPDATA "Firaxis Games\Sid Meier's Civilization VI\Logs\Lua.log"

function Tuner($state, $file, $timeout) {
    Push-Location $mcp
    $out = & uv run python tuner_exec.py $state $file $timeout 2>&1 | ForEach-Object { "$_" -replace "`0", "" }
    Pop-Location
    return ($out -join "`n")
}
function Wait-Port($seconds) {
    $t0 = Get-Date
    while (((Get-Date) - $t0).TotalSeconds -lt $seconds) {
        $c = New-Object System.Net.Sockets.TcpClient
        try { $c.Connect('127.0.0.1', 4318); $c.Close(); return $true } catch { Start-Sleep 2 }
    }
    return $false
}

Stop-ScheduledTask -TaskName Civ6Mcp -ErrorAction SilentlyContinue
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*civ6-mcp*" } | Stop-Process -Force
Get-Process CivilizationVI -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 12   # Steam deregisters the game
Start-ScheduledTask -TaskName Civ6Launch
if (-not (Wait-Port 240)) { "FAILED: FireTuner port did not open"; return }
"port open after launch"

# The copyright screen, then the main menu. Each state shows up only once the screen before it is gone.
$t0 = Get-Date; $menu = $false
$noop = Join-Path $env:TEMP 'bench-noop.lua'; Set-Content -Path $noop -Value 'print("noop")'
while (((Get-Date) - $t0).TotalSeconds -lt 180 -and -not $menu) {
    $states = Tuner '__none__' $noop 6
    if ($states -match "'MainMenu'") { $menu = $true; break }
    if ($states -match "'IntroScreen'") { Tuner 'IntroScreen' (Join-Path $lua 'accept-eula.lua') 6 | Out-Null }
    Start-Sleep 3
}
if (-not $menu) { "FAILED: no MainMenu state"; return }
"main menu up"

$file = Join-Path $env:TEMP 'bench-new-game.lua'
Set-Content -Path $file -Encoding UTF8 -Value ("SPEED = '$Speed'`nGAME_SEED = $Seed`nMAP_SEED = $Seed`n" + (Get-Content (Join-Path $lua 'new-game.lua') -Raw))
$started = Get-Date
Tuner 'MainMenu' $file 20

while (((Get-Date) - $started).TotalSeconds -lt 300) {
    if ((Test-Path $log) -and (Get-Item $log).LastWriteTime -gt $started -and (Select-String -Path $log -Pattern 'OnLoadGameViewStateDone' -Quiet)) {
        "LOADED after $([int]((Get-Date) - $started).TotalSeconds) s: click BEGIN GAME next"; return
    }
    if (-not (Get-Process CivilizationVI -ErrorAction SilentlyContinue)) { "FAILED: game exited"; return }
    Start-Sleep 3
}
"FAILED: map did not load in 300 s"

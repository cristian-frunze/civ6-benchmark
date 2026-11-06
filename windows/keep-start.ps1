# Keep the turn-1 autosave of a game made by windows/new-start.ps1 as a named start, for run_game.py --start-save.
# Prepend: $Name = 'BENCH_PANGAEA_ONLINE_T1'
if (-not $Name) { "FAILED: set `$Name"; return }
$single = Join-Path ([Environment]::GetFolderPath('MyDocuments')) "My Games\Sid Meier's Civilization VI\Saves\Single"
$src = Join-Path $single 'auto\AutoSave_0001.Civ6Save'
$keep = Join-Path $env:USERPROFILE 'civ6-bench\starts'
New-Item -ItemType Directory -Force -Path $keep | Out-Null
Copy-Item $src (Join-Path $keep "$Name.Civ6Save") -Force
Get-Item $src, (Join-Path $keep "$Name.Civ6Save") | Select-Object FullName, Length, LastWriteTime | Format-List | Out-String

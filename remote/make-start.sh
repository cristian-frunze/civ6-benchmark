#!/usr/bin/env bash
# make-start <name> [speed] [difficulty] [seed]: make a new single-player game on the game PC and keep its turn-1
# autosave as a named start, %USERPROFILE%\civ6-bench\starts\<name>.Civ6Save, for run_game.py --start-save.
# It takes over the PC (stops the civ6-mcp server, kills the game): run it only between games.
#   remote/make-start.sh BENCH_PANGAEA_ONLINE_DEITY_T1 GAMESPEED_ONLINE DIFFICULTY_DEITY
# Same seed, same map and leaders as the other starts; the difficulty changes only the AI's bonuses.
set -euo pipefail
name=$1; speed=${2:-GAMESPEED_ONLINE}; difficulty=${3:-DIFFICULTY_PRINCE}; seed=${4:-20261106}
here=$(cd "$(dirname "$0")" && pwd); win=$here/../windows
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT

# 1. A new game from the main menu, up to the leader screen (windows/new-start.ps1).
{ echo "\$Speed = '$speed'; \$Seed = $seed; \$Extra = \"DIFFICULTY = '$difficulty'\""; cat "$win/new-start.ps1"; } > "$t/ns.ps1"
out=$("$here/zexec.sh" "$t/ns.ps1" 900)
echo "$out"
grep -q "LOADED" <<<"$out" || { echo "make-start: the new game did not load"; exit 1; }

# 2. BEGIN GAME (the leader screen's button, physical screen point on the Zenbook's top screen), then wait for the
#    turn-1 autosave the game writes as the first turn starts.
started=$(date +%s)
sleep 15
{ echo '$Points = @(,@(1000,1612))'; cat "$win/click-at.ps1"; } > "$t/click.ps1"
"$here/zexec.sh" "$t/click.ps1" 30
cat > "$t/auto.ps1" <<EOF
\$f = Join-Path ([Environment]::GetFolderPath('MyDocuments')) "My Games\\Sid Meier's Civilization VI\\Saves\\Single\\auto\\AutoSave_0001.Civ6Save"
if ((Test-Path \$f) -and ((Get-Item \$f).LastWriteTimeUtc -gt [DateTimeOffset]::FromUnixTimeSeconds($started).UtcDateTime)) { 'NEW' } else { 'OLD' }
EOF
for _ in $(seq 60); do
  "$here/zps.sh" "$t/auto.ps1" | grep -q '^NEW' && break
  sleep 5
done
"$here/zps.sh" "$t/auto.ps1" | grep -q '^NEW' || { echo "make-start: no new turn-1 autosave"; exit 1; }

# 3. Keep it (windows/keep-start.ps1).
{ echo "\$Name = '$name'"; cat "$win/keep-start.ps1"; } > "$t/keep.ps1"
"$here/zps.sh" "$t/keep.ps1"
echo "make-start: kept $name ($speed, $difficulty, seed $seed)"

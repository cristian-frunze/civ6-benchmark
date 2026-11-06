# One-time setup for hotseat games (Opus vs Opus): the hotseat fork of civ6-mcp (Johnor12/civ6-mcp, MIT, pinned)
# and its MCP Bridge UI mod. Then copy civ_mcp_hotseat.py, bench_compat.py and base-game-compat.lua into the checkout.
# The bridge mod is pure UI (AffectsSavedGames=0): it changes no rules and no saves, and it idles in single player.
$ErrorActionPreference = 'Continue'; $ProgressPreference = 'SilentlyContinue'
$root = "$env:USERPROFILE\civ6-bench"
$dir = Join-Path $root 'civ6-mcp-hotseat'
if (-not (Test-Path $dir)) { git -c core.symlinks=false clone -q https://github.com/Johnor12/civ6-mcp.git $dir 2>&1 | Out-String }
Set-Location $dir
git -c advice.detachedHead=false checkout -q 0af10ed 2>&1 | Out-String
"HEAD: " + (git log -1 --format='%h %cs')
$env:UV_PYTHON_PREFERENCE = 'only-managed'
uv sync 2>&1 | Select-Object -Last 4 | Out-String
uv run python scripts/install_bridge_mod.py 2>&1 | Out-String

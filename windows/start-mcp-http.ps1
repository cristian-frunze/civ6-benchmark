# Start the civ6-mcp HTTP server (windows/civ_mcp_http.py) in the desktop session, via the Civ6Mcp scheduled task,
# so its game-recovery tools (kill, relaunch, menu clicks) can reach the game window. Logs to logs\mcp-http.log.
$bench = Join-Path $env:USERPROFILE 'civ6-bench'
$cfgPath = Join-Path $bench 'mcp-env.json'   # optional: {"CIV_MCP_AGENT_MODEL": "claude-opus-5-5", ...}; "CIV_MCP_SERVER": "hotseat" picks the hotseat server
$env:CIV_MCP_DISABLE_LUA = '1'               # same as CivBench: agents use the built-in tools only
$env:CIV_MCP_PORT = '8771'
if (Test-Path $cfgPath) { (Get-Content $cfgPath -Raw | ConvertFrom-Json).PSObject.Properties | ForEach-Object { Set-Item "env:$($_.Name)" $_.Value } }
New-Item -ItemType Directory -Force -Path (Join-Path $bench 'logs') | Out-Null
if ($env:CIV_MCP_SERVER -eq 'hotseat') {
  # Hotseat games (FireTuner is off in multiplayer): the hotseat fork over the MCP Bridge mod, windows/civ_mcp_hotseat.py
  Set-Location (Join-Path $bench 'civ6-mcp-hotseat')
  & uv run python civ_mcp_hotseat.py *>> (Join-Path $bench 'logs\mcp-hotseat.log')
} else {
  Set-Location (Join-Path $bench 'civ6-mcp')
  & uv run --extra launcher-windows python civ_mcp_http.py *>> (Join-Path $bench 'logs\mcp-http.log')
}

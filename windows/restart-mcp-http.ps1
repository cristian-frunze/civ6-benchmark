# Restart the civ6-mcp HTTP server (Civ6Mcp task). Stopping it drops the FireTuner connection abruptly, which
# civ6-mcp warns can crash the game, so do this between games or when the game is idle.
Stop-ScheduledTask -TaskName Civ6Mcp -ErrorAction SilentlyContinue
# Both servers (civ_mcp_http.py, civ_mcp_hotseat.py) run as a venv launcher plus the interpreter it starts: stop both.
Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Where-Object { $_.CommandLine -like '*civ_mcp_*.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep 3
Start-ScheduledTask -TaskName Civ6Mcp
$t0 = Get-Date
while (((Get-Date) - $t0).TotalSeconds -lt 150) {   # the hotseat server takes about a minute
  $c = New-Object System.Net.Sockets.TcpClient
  try { $c.Connect('127.0.0.1', 8771); $c.Close(); break } catch { Start-Sleep 1 }
}
"restarted; game running: $([bool](Get-Process CivilizationVI -ErrorAction SilentlyContinue))"

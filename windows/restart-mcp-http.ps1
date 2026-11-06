# Restart the civ6-mcp HTTP server (Civ6Mcp task). Stopping it drops the FireTuner connection abruptly, which
# civ6-mcp warns can crash the game, so do this between games or when the game is idle.
Stop-ScheduledTask -TaskName Civ6Mcp -ErrorAction SilentlyContinue
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*civ6-mcp*" } | Stop-Process -Force
Start-Sleep 3
Start-ScheduledTask -TaskName Civ6Mcp
$t0 = Get-Date
while (((Get-Date) - $t0).TotalSeconds -lt 60) {
  $c = New-Object System.Net.Sockets.TcpClient
  try { $c.Connect('127.0.0.1', 8771); $c.Close(); break } catch { Start-Sleep 1 }
}
"restarted; game running: $([bool](Get-Process CivilizationVI -ErrorAction SilentlyContinue))"

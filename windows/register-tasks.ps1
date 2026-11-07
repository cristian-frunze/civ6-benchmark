$ps = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
foreach ($t in @(@{n='Civ6Shot'; f='screenshot.ps1'}, @{n='Civ6Launch'; f='launch-civ.ps1'}, @{n='Civ6Click'; f='click.ps1'}, @{n='Civ6Exec'; f='exec-runner.ps1'}, @{n='Civ6Mcp'; f='start-mcp-http.ps1'}, @{n='Civ6Archive'; f='archive-turn.ps1'}, @{n='Civ6Awake'; f='keep-awake.ps1'})) {
  $a = New-ScheduledTaskAction -Execute $ps -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File $env:USERPROFILE\civ6-bench\$($t.f)"
  $p = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
  $s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
  Register-ScheduledTask -TaskName $t.n -Action $a -Principal $p -Settings $s -Force | Out-Null
  "registered $($t.n)"
}
# The keep-awake loop also starts at logon, and now.
Set-ScheduledTask -TaskName Civ6Awake -Trigger (New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)) | Out-Null
Start-ScheduledTask -TaskName Civ6Awake

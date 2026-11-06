$ps = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
foreach ($t in @(@{n='Civ6Shot'; f='screenshot.ps1'}, @{n='Civ6Launch'; f='launch-civ.ps1'}, @{n='Civ6Click'; f='click.ps1'})) {
  $a = New-ScheduledTaskAction -Execute $ps -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File $env:USERPROFILE\civ6-bench\$($t.f)"
  $p = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
  Register-ScheduledTask -TaskName $t.n -Action $a -Principal $p -Force | Out-Null
  "registered $($t.n)"
}

# Click a point in the Civ 6 window's client area. Reads "fx fy" (fractions 0-1) from click.txt.
# Runs inside the user's session via the Civ6Click scheduled task. Logs to click.log.
$dir = "$env:USERPROFILE\civ6-bench"
$log = "$dir\click.log"
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public class W {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, IntPtr e);
}
'@
[W]::SetProcessDPIAware() | Out-Null
$f = (Get-Content "$dir\click.txt" -Raw).Trim() -split '\s+'
$p = Get-Process CivilizationVI_DX12, CivilizationVI -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $p) { "$(Get-Date -f s) no civ window" | Add-Content $log; exit 1 }
$h = $p.MainWindowHandle
[W]::ShowWindow($h, 9) | Out-Null
[W]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 300
$r = New-Object W+RECT; [W]::GetClientRect($h, [ref]$r) | Out-Null
$o = New-Object W+POINT; [W]::ClientToScreen($h, [ref]$o) | Out-Null
$x = [int]($o.X + [double]$f[0] * $r.R); $y = [int]($o.Y + [double]$f[1] * $r.B)
[W]::SetCursorPos($x, $y) | Out-Null
Start-Sleep -Milliseconds 150
[W]::mouse_event(0x0002, 0, 0, 0, [IntPtr]::Zero); Start-Sleep -Milliseconds 60
[W]::mouse_event(0x0004, 0, 0, 0, [IntPtr]::Zero)
"$(Get-Date -f s) clicked $x,$y client=$($r.R)x$($r.B) origin=$($o.X),$($o.Y) frac=$($f -join ' ')" | Add-Content $log

# Click a point in the Civ 6 window's client area. Reads "fx fy" (fractions 0-1 of the client area) from
# %USERPROFILE%\civ6-bench\click.txt. Runs inside the user's desktop session via the Civ6Click scheduled task.
# Uses SendInput with absolute coordinates, after forcing the game window to the foreground (a scheduled
# task is a background process, so Windows' foreground lock has to be released with an ALT tap first).
$dir = "$env:USERPROFILE\civ6-bench"
$log = "$dir\click.log"
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public class W {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
  [StructLayout(LayoutKind.Sequential)] public struct MOUSEINPUT { public int dx, dy; public uint mouseData, dwFlags, time; public IntPtr extra; }
  [StructLayout(LayoutKind.Sequential)] public struct INPUT { public uint type; public MOUSEINPUT mi; }
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, IntPtr extra);
  [DllImport("user32.dll")] public static extern int GetSystemMetrics(int i);
  [DllImport("user32.dll")] public static extern uint SendInput(uint n, INPUT[] inputs, int size);
  public static void Mouse(int x, int y, uint flags) {
    int vx = GetSystemMetrics(76), vy = GetSystemMetrics(77), vw = GetSystemMetrics(78), vh = GetSystemMetrics(79);
    INPUT i = new INPUT(); i.type = 0;
    i.mi.dx = (int)Math.Round((x - vx) * 65535.0 / (vw - 1));
    i.mi.dy = (int)Math.Round((y - vy) * 65535.0 / (vh - 1));
    i.mi.dwFlags = flags | 0x8000 | 0x4000;  // ABSOLUTE | VIRTUALDESK
    SendInput(1, new INPUT[] { i }, Marshal.SizeOf(typeof(INPUT)));
  }
}
'@
[W]::SetProcessDPIAware() | Out-Null
$f = (Get-Content "$dir\click.txt" -Raw).Trim() -split '\s+'
$p = Get-Process CivilizationVI_DX12, CivilizationVI -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $p) { "$(Get-Date -f s) no civ window" | Add-Content $log; exit 1 }
$h = $p.MainWindowHandle
[W]::ShowWindow($h, 9) | Out-Null
[W]::keybd_event(0x12, 0, 0, [IntPtr]::Zero); [W]::keybd_event(0x12, 0, 2, [IntPtr]::Zero)  # ALT tap releases the foreground lock
[W]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 400
$fg = ([W]::GetForegroundWindow() -eq $h)
$r = New-Object W+RECT; [W]::GetClientRect($h, [ref]$r) | Out-Null
$o = New-Object W+POINT; [W]::ClientToScreen($h, [ref]$o) | Out-Null
$x = [int]($o.X + [double]$f[0] * $r.R); $y = [int]($o.Y + [double]$f[1] * $r.B)
[W]::Mouse($x, $y, 0x0001)            # move
Start-Sleep -Milliseconds 250
[W]::Mouse($x, $y, 0x0001)            # move again so the UI registers hover
Start-Sleep -Milliseconds 150
[W]::Mouse($x, $y, 0x0002)            # left down
Start-Sleep -Milliseconds 80
[W]::Mouse($x, $y, 0x0004)            # left up
"$(Get-Date -f s) clicked $x,$y foreground=$fg client=$($r.R)x$($r.B) origin=$($o.X),$($o.Y) frac=$($f -join ' ')" | Add-Content $log

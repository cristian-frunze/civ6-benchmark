# Click physical screen points in the desktop session (any window). Set $Points before this body, e.g.
#   $Points = @(@(1077,767), @(1547,1225))   (one point: @(,@(x,y)), or PowerShell flattens it)
# Brings the window under each point to the front first (ALT tap releases Windows' foreground lock).
# Each click starts 40 px away: the game takes a click only on a button it saw the mouse move onto, so a click with
# the cursor already on the spot (left there by the last click, as BEGIN GAME sits at the same point in every new
# game) is ignored.
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public class CA {
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
  [StructLayout(LayoutKind.Sequential)] public struct MOUSEINPUT { public int dx, dy; public uint mouseData, dwFlags, time; public IntPtr extra; }
  [StructLayout(LayoutKind.Sequential)] public struct INPUT { public uint type; public MOUSEINPUT mi; }
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(POINT p);
  [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr h, uint f);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, IntPtr extra);
  [DllImport("user32.dll")] public static extern int GetSystemMetrics(int i);
  [DllImport("user32.dll")] public static extern uint SendInput(uint n, INPUT[] inputs, int size);
  public static void Mouse(int x, int y, uint flags) {
    int vx = GetSystemMetrics(76), vy = GetSystemMetrics(77), vw = GetSystemMetrics(78), vh = GetSystemMetrics(79);
    INPUT i = new INPUT(); i.type = 0;
    i.mi.dx = (int)Math.Round((x - vx) * 65535.0 / (vw - 1));
    i.mi.dy = (int)Math.Round((y - vy) * 65535.0 / (vh - 1));
    i.mi.dwFlags = flags | 0x8000 | 0x4000;
    SendInput(1, new INPUT[] { i }, Marshal.SizeOf(typeof(INPUT)));
  }
}
'@
[CA]::SetProcessDPIAware() | Out-Null
foreach ($pt in $Points) {
  $p = New-Object CA+POINT; $p.X = $pt[0]; $p.Y = $pt[1]
  $h = [CA]::GetAncestor([CA]::WindowFromPoint($p), 2)
  [CA]::keybd_event(0x12, 0, 0, [IntPtr]::Zero); [CA]::keybd_event(0x12, 0, 2, [IntPtr]::Zero)
  [CA]::SetForegroundWindow($h) | Out-Null
  Start-Sleep -Milliseconds 300
  [CA]::Mouse($pt[0] + 40, $pt[1] + 40, 0x0001); Start-Sleep -Milliseconds 200
  [CA]::Mouse($pt[0], $pt[1], 0x0001); Start-Sleep -Milliseconds 120
  [CA]::Mouse($pt[0], $pt[1], 0x0002); Start-Sleep -Milliseconds 80
  [CA]::Mouse($pt[0], $pt[1], 0x0004); Start-Sleep -Milliseconds 500
  "clicked $($pt[0]),$($pt[1]) window=$h"
}

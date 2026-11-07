# Keep the game PC's desktop live while games run (Civ6Awake task, desktop session). Screensavers that some vendor
# software re-enables (Asus "OLED Care" on the Zenbook) take over the input desktop after idle minutes; screenshots
# and clicks then fail, and civ6-mcp cannot click through the menus to reload a save after a hang.
# Holds ES_DISPLAY_REQUIRED for as long as it runs, moves the mouse by 0 pixels every 50 s (resets the idle timer,
# changes nothing on screen), and stops a screensaver that is running anyway. Stop the task to end it.
Add-Type @'
using System; using System.Runtime.InteropServices;
public class Awake {
  [StructLayout(LayoutKind.Sequential)] public struct MOUSEINPUT { public int dx, dy; public uint mouseData, dwFlags, time; public IntPtr extra; }
  [StructLayout(LayoutKind.Sequential)] public struct INPUT { public uint type; public MOUSEINPUT mi; }
  [DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);
  [DllImport("user32.dll")] public static extern uint SendInput(uint n, INPUT[] i, int size);
  public static void Nudge() { INPUT i = new INPUT(); i.type = 0; i.mi.dwFlags = 0x0001; SendInput(1, new INPUT[] { i }, Marshal.SizeOf(typeof(INPUT))); }
}
'@
$log = Join-Path $env:USERPROFILE 'civ6-bench\logs\keep-awake.log'
[Awake]::SetThreadExecutionState(0x80000003) | Out-Null   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
while ($true) {
    [Awake]::Nudge()
    foreach ($p in Get-Process | Where-Object { $_.Path -like '*.scr' }) {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Add-Content $log "$(Get-Date -Format s) stopped screensaver $($p.Path)"
    }
    Start-Sleep -Seconds 50
}

# Screenshot of every screen, scaled down to a JPEG for quick checks. Run in the desktop session (remote/zexec.sh).
param([string]$Out = "$env:USERPROFILE\civ6-bench\shots\small.jpg", [double]$Scale = 0.4)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type 'using System.Runtime.InteropServices; public class DpiS { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }'
[DpiS]::SetProcessDPIAware() | Out-Null
$b = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
$w = [int]($b.Width * $Scale); $h = [int]($b.Height * $Scale)
$sm = New-Object System.Drawing.Bitmap $w, $h
$g2 = [System.Drawing.Graphics]::FromImage($sm); $g2.InterpolationMode = 'HighQualityBicubic'; $g2.DrawImage($bmp, 0, 0, $w, $h)
New-Item -ItemType Directory -Force -Path (Split-Path $Out) | Out-Null
$sm.Save($Out, [System.Drawing.Imaging.ImageFormat]::Jpeg)
$g.Dispose(); $g2.Dispose(); $bmp.Dispose(); $sm.Dispose()
"saved $Out ${w}x${h}"

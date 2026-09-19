<#
.SYNOPSIS
    Saves a PNG of a top-level window, matched by window title.

.EXAMPLE
    pwsh -File scripts/screenshot-window.ps1 -Out shot.png -TitleLike 'Minecraft*'
#>
param(
    [Parameter(Mandatory = $true)][string]$Out,
    [string]$TitleLike = 'Minecraft*'
)

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class NativeWin {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool GetCursorInfo(ref CURSORINFO ci);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
    [StructLayout(LayoutKind.Sequential)] public struct CURSORINFO { public int Size, Flags; public IntPtr Cursor; public POINT Pos; }
}
"@
Add-Type -AssemblyName System.Windows.Forms

# Without this the captured rectangle is wrong on scaled displays.
[NativeWin]::SetProcessDPIAware() | Out-Null

$proc = Get-Process | Where-Object { $_.MainWindowTitle -like $TitleLike } | Select-Object -First 1
if (-not $proc) {
    Write-Error "No window matching '$TitleLike'"
    exit 1
}

[NativeWin]::SetForegroundWindow($proc.MainWindowHandle) | Out-Null
Start-Sleep -Milliseconds 800

# In the world the game hides and grabs the cursor; any open screen (inventory, pause) shows it.
# A visible cursor therefore means a screen is up, and Escape closes it without side effects.
$ci = New-Object NativeWin+CURSORINFO
$ci.Size = [System.Runtime.InteropServices.Marshal]::SizeOf($ci)
[NativeWin]::GetCursorInfo([ref]$ci) | Out-Null
if ($ci.Flags -band 1) {
    Write-Output "a screen was open (cursor visible); sending Escape before the capture"
    [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
    Start-Sleep -Milliseconds 600
}

$rect = New-Object NativeWin+RECT
[NativeWin]::GetWindowRect($proc.MainWindowHandle, [ref]$rect) | Out-Null
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top

$bitmap = New-Object System.Drawing.Bitmap($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
$bitmap.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

Write-Output "saved $Out (${width}x${height}) from '$($proc.MainWindowTitle)'"

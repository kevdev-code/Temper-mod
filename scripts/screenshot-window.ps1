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
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
}
"@

# Without this the captured rectangle is wrong on scaled displays.
[NativeWin]::SetProcessDPIAware() | Out-Null

$proc = Get-Process | Where-Object { $_.MainWindowTitle -like $TitleLike } | Select-Object -First 1
if (-not $proc) {
    Write-Error "No window matching '$TitleLike'"
    exit 1
}

[NativeWin]::SetForegroundWindow($proc.MainWindowHandle) | Out-Null
Start-Sleep -Milliseconds 800

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

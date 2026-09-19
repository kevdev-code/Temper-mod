<#
.SYNOPSIS
    Saves a PNG of a top-level window, matched by window title.

.EXAMPLE
    pwsh -File scripts/screenshot-window.ps1 -Out shot.png -ProcessId 1234
#>
param(
    [Parameter(Mandatory = $true)][string]$Out,
    [string]$TitleLike = 'Minecraft*',
    [int]$ProcessId = 0
)

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class NativeWin {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
}
"@

# Without this the captured rectangle is wrong on scaled displays.
[NativeWin]::SetProcessDPIAware() | Out-Null

# A process id is exact. Matching on the title alone can pick another Minecraft window, such as one
# an earlier run left at the menu, and quietly screenshot that instead of the client under test.
if ($ProcessId -gt 0) {
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc -or $proc.MainWindowHandle -eq 0) {
        Write-Error "Process $ProcessId has no window"
        exit 1
    }
} else {
    $windows = @(Get-Process | Where-Object { $_.MainWindowTitle -like $TitleLike })
    if ($windows.Count -eq 0) {
        Write-Error "No window matching '$TitleLike'"
        exit 1
    }
    if ($windows.Count -gt 1) {
        Write-Output ("warning: {0} windows match; using the first" -f $windows.Count)
    }
    $proc = $windows[0]
}

# CopyFromScreen reads the screen, not the window, so anything overlapping the window lands in the
# shot instead. Raise it and pin it on top, then check it really is the foreground before capturing.
$handle = $proc.MainWindowHandle
[NativeWin]::ShowWindow($handle, 9) | Out-Null            # SW_RESTORE, in case it is minimised
[NativeWin]::BringWindowToTop($handle) | Out-Null
[NativeWin]::SetForegroundWindow($handle) | Out-Null
[NativeWin]::SetWindowPos($handle, [IntPtr]::new(-1), 0, 0, 0, 0, 0x0043) | Out-Null   # HWND_TOPMOST
Start-Sleep -Milliseconds 1200
if ([NativeWin]::GetForegroundWindow() -ne $handle) {
    Write-Output "warning: pid $($proc.Id) is not the foreground window; the capture may show what is on top of it"
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
[NativeWin]::SetWindowPos($handle, [IntPtr]::new(-2), 0, 0, 0, 0, 0x0043) | Out-Null   # HWND_NOTOPMOST
$bitmap.Dispose()

Write-Output "saved $Out (${width}x${height}) from pid $($proc.Id) '$($proc.MainWindowTitle)'"

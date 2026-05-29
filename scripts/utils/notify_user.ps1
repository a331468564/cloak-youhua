param(
    [string]$Title = "Codex",
    [string]$Message = "Task needs your attention.",
    [int]$TimeoutMs = 8000,
    [string]$AppId = "Codex.Project.Notifier"
)

$ErrorActionPreference = "Stop"

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class AppUserModelId
{
    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    private static extern int SetCurrentProcessExplicitAppUserModelID(string appID);

    public static void Set(string appID)
    {
        int hr = SetCurrentProcessExplicitAppUserModelID(appID);
        if (hr != 0)
        {
            Marshal.ThrowExceptionForHR(hr);
        }
    }
}
"@

function Show-ToastNotification {
    param(
        [string]$ToastTitle,
        [string]$ToastMessage,
        [string]$ToastAppId
    )

    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

    $template = @"
<toast>
  <visual>
    <binding template="ToastGeneric">
      <text>$([System.Security.SecurityElement]::Escape($ToastTitle))</text>
      <text>$([System.Security.SecurityElement]::Escape($ToastMessage))</text>
    </binding>
  </visual>
</toast>
"@

    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($template)
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    [AppUserModelId]::Set($ToastAppId)
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($ToastAppId)
    $notifier.Show($toast)
}

function Show-BalloonNotification {
    param(
        [string]$BalloonTitle,
        [string]$BalloonMessage,
        [int]$BalloonTimeoutMs
    )

    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    $notify = New-Object System.Windows.Forms.NotifyIcon
    $notify.Icon = [System.Drawing.SystemIcons]::Information
    $notify.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
    $notify.BalloonTipTitle = $BalloonTitle
    $notify.BalloonTipText = $BalloonMessage
    $notify.Visible = $true

    try {
        $notify.ShowBalloonTip($BalloonTimeoutMs)
        Start-Sleep -Milliseconds ([Math]::Min([Math]::Max($BalloonTimeoutMs, 1000), 10000))
    }
    finally {
        $notify.Visible = $false
        $notify.Dispose()
    }
}

try {
    Show-ToastNotification -ToastTitle $Title -ToastMessage $Message -ToastAppId $AppId
}
catch {
    Show-BalloonNotification -BalloonTitle $Title -BalloonMessage $Message -BalloonTimeoutMs $TimeoutMs
}

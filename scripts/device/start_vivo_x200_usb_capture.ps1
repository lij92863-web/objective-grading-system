[CmdletBinding()]
param(
    [string]$Serial = "",
    [ValidateRange(1, 65535)]
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$CheckScript = Join-Path $PSScriptRoot "check_android_usb_capture.ps1"
$HealthUrl = "http://127.0.0.1:$Port/mobile-capture/health.json"
$MobileUrl = "http://localhost:$Port/mobile-capture"

function Test-MobileCaptureHealth {
    try {
        $response = Invoke-RestMethod -Uri $HealthUrl -Method Get -TimeoutSec 2
        return (
            $response.ok -eq $true -and
            $response.service -eq "objective-grading-mobile-capture" -and
            $response.transport -eq "adb-reverse-compatible" -and
            $response.real_recognition_enabled -eq $false
        )
    } catch {
        return $false
    }
}

function Test-LocalPortOpen {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $task = $client.ConnectAsync("127.0.0.1", $Port)
        if (-not $task.Wait(500)) {
            return $false
        }
        return $client.Connected
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Wait-MobileCaptureHealth {
    $deadline = [DateTime]::UtcNow.AddSeconds(25)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-MobileCaptureHealth) {
            return $true
        }
        Start-Sleep -Milliseconds 350
    }
    return $false
}

try {
    Write-Host "正在检查 vivo X200 USB 调试连接…" -ForegroundColor Cyan
    $device = & $CheckScript -Serial $Serial -PassThru
    if ($null -eq $device) {
        throw "设备检查没有返回可用设备。"
    }

    if (Test-MobileCaptureHealth) {
        Write-Host "本地采集服务已在 127.0.0.1:$Port 运行，不重复启动。" -ForegroundColor Green
    } else {
        if (Test-LocalPortOpen) {
            throw "端口 $Port 已被其他服务占用，且健康检查不匹配。为保护用户进程，脚本不会终止它。"
        }
        $python = Get-Command python -ErrorAction SilentlyContinue
        if ($null -eq $python) {
            throw "未找到 Python，无法启动 web_app.py。"
        }
        Write-Host "正在后台启动本地采集服务…"
        $process = Start-Process `
            -FilePath $python.Source `
            -ArgumentList @("web_app.py", "$Port") `
            -WorkingDirectory $RepoRoot `
            -WindowStyle Hidden `
            -PassThru
        Write-Host "已启动服务进程 PID $($process.Id)；脚本不会擅自终止它。"
        if (-not (Wait-MobileCaptureHealth)) {
            throw "本地服务启动后未通过健康检查。请在仓库目录手动运行 python web_app.py 查看错误。"
        }
    }

    $adb = $device.AdbPath
    $selectedSerial = $device.Serial
    Write-Host "正在建立 adb reverse tcp:$Port tcp:$Port…"
    $reverseOutput = & $adb -s $selectedSerial reverse "tcp:$Port" "tcp:$Port" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "adb reverse 失败：$($reverseOutput -join ' ')"
    }
    $reverseList = & $adb -s $selectedSerial reverse --list 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "无法核验 adb reverse：$($reverseList -join ' ')"
    }
    $mapping = "tcp:$Port tcp:$Port"
    if (-not (($reverseList -join "`n").Contains($mapping))) {
        throw "adb reverse --list 中没有找到 $mapping，已停止打开页面。"
    }

    Write-Host "ADB reverse 已核验。正在尝试在手机打开采集页…" -ForegroundColor Green
    $viewOutput = & $adb -s $selectedSerial shell am start `
        -a android.intent.action.VIEW `
        -d $MobileUrl 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "无法自动打开手机浏览器：$($viewOutput -join ' ')"
    }
    Write-Host "手机备用地址：$MobileUrl" -ForegroundColor Yellow
    Write-Host "电脑健康检查：$HealthUrl"
    Write-Host "提示：数据线只负责 ADB 转发，不是 Windows 直接调用手机摄像头。"
} catch {
    Write-Error $_.Exception.Message
    exit 1
}

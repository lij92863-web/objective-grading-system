# vivo X200 USB 采集安装与启动

## 前提

- Windows 电脑已安装 Python，且本仓库现有依赖可运行。
- 用户自行安装 Android Platform-Tools，并能运行 `adb`。
- vivo X200 已解锁、开启开发者选项和 USB 调试，并由用户在手机上确认本电脑授权。
- 使用支持数据传输的 USB 线。

仓库不会下载 ADB、安装驱动、修改系统 PATH、修改手机设置或绕过授权。`local-tools/` 被 Git 忽略，可由用户自行放置 Platform-Tools。

## ADB 查找顺序

启动脚本依次检查：

1. PATH 中的 `adb`；
2. 仓库 `local-tools/platform-tools/adb.exe`；
3. `%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe`。

## 启动

双击仓库根目录的 `启动手机USB拍摄.bat`，或在 PowerShell 中运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\device\start_vivo_x200_usb_capture.ps1
```

脚本会：

1. 检查 ADB 和设备状态；
2. 要求在多设备场景明确选择 serial；
3. 检查 `http://127.0.0.1:8765/mobile-capture/health.json`；
4. 仅在正确服务尚未运行时启动 `python web_app.py`；
5. 执行并核验 `adb reverse tcp:8765 tcp:8765`；
6. 尝试用 Android VIEW intent 打开 `http://localhost:8765/mobile-capture`；
7. 同时打印可手工输入的备用地址。

脚本不会终止用户已有 Python 进程，也不会重复启动已通过健康检查的服务。

## 常见状态

- 没有设备：连接 vivo X200、解锁手机并开启 USB 调试。
- `unauthorized`：查看手机并点击“允许此电脑进行 USB 调试”。
- `offline`：重新插拔数据线或重启 ADB 后再次检查。
- 多台设备：使用 `-Serial <serial>` 明确选择，脚本不会随机选择。

可只运行诊断：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\device\check_android_usb_capture.ps1
```

## 传输事实

电脑服务始终只监听 `127.0.0.1:8765`。ADB reverse 把手机的 `localhost:8765` 转发到电脑本机；这不是 Windows 直接调用 vivo X200 摄像头，也不需要把服务开放为 `0.0.0.0`。

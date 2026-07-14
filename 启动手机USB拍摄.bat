@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\device\start_vivo_x200_usb_capture.ps1" %*
if errorlevel 1 (
  echo.
  echo 启动未完成，请按上方提示检查 USB、授权、ADB 或端口。
  pause
)
endlocal

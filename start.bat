@echo off
chcp 65001 > nul
title 收益分配测算系统 - 快速启动

echo =====================================
echo    收益分配测算系统 - 快速启动
echo =====================================
echo.

:: 检查端口是否被占用
echo 检查端口状态...
netstat -ano | findstr :5000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️ 端口5000已被占用，正在终止占用进程...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :5000') do (
        taskkill /pid %%i /f >nul 2>&1
    )
    timeout /t 2 >nul
)

echo 🚀 启动收益分配测算系统...
echo 📱 访问地址: http://localhost:5000
echo.
echo ⚠️ 请勿关闭此窗口，关闭将停止服务
echo.

:: 延迟启动浏览器
start "" cmd /c "timeout /t 2 >nul && start http://localhost:5000"

:: 启动应用
python app.py

echo.
echo ⚠️ 服务器已停止
pause 
@echo off
chcp 65001 > nul
title 收益分配测算系统 - 一键部署脚本

echo =====================================
echo    收益分配测算系统 - 一键部署
echo =====================================
echo.

:: 检查Python是否已安装
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X Python未安装，请先安装Python 3.8或更高版本
    echo 请访问 https://www.python.org/downloads/ 下载安装Python
    pause
    exit /b 1
) else (
    echo √ Python环境检查通过
)
echo.

:: 检查pip是否可用
echo [2/6] 检查pip包管理器...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X pip不可用，请检查Python安装
    pause
    exit /b 1
) else (
    echo √ pip包管理器可用
)
echo.

:: 升级pip到最新版本
echo [3/6] 升级pip到最新版本...
python -m pip install --upgrade pip --quiet
if %errorlevel% neq 0 (
    echo ! pip升级失败，继续安装依赖...
) else (
    echo √ pip升级成功
)
echo.

:: 安装Python依赖
echo [4/6] 安装Python依赖包...
echo 正在安装依赖包，请稍候...

:: 先尝试使用国内镜像源安装
echo 尝试使用清华大学镜像源...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/ --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo ! 镜像源安装失败，尝试使用官方源...
    pip install -r requirements.txt --quiet --disable-pip-version-check
    if %errorlevel% neq 0 (
        echo X 依赖安装失败
        echo.
        echo 可能的解决方案:
        echo 1. 检查网络连接
        echo 2. 手动安装依赖: pip install flask pandas numpy openpyxl
        echo 3. 使用虚拟环境: python -m venv venv
        echo 4. 更新Python版本或降级到Python 3.11
        echo.
        pause
        exit /b 1
    ) else (
        echo √ 官方源安装成功
    )
) else (
    echo √ 镜像源安装成功
)
echo.

:: 检查端口是否被占用
echo [5/6] 检查端口占用情况...
netstat -ano | findstr :5000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ! 端口5000已被占用，将尝试终止占用进程...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :5000') do (
        echo 终止进程 %%i
        taskkill /pid %%i /f >nul 2>&1
    )
)
echo √ 端口5000可用
echo.

:: 启动应用
echo [6/6] 启动收益分配测算系统...
echo 正在启动服务器...
echo 服务器地址: http://localhost:5000
echo 使用说明:
echo    1. 填写基本投资参数
echo    2. 输入各年度净现金流
echo    3. 选择分配模式
echo    4. 执行计算并查看结果
echo    5. 导出Excel报告
echo.
echo 注意：请勿关闭此窗口，关闭将停止服务
echo.

:: 启动浏览器（延迟2秒等待服务器启动）
start "" cmd /c "timeout /t 2 >nul && start http://localhost:5000"

:: 启动Flask应用
python app.py

:: 如果程序异常退出，暂停以便查看错误信息
echo.
echo ! 服务器已停止运行
pause 
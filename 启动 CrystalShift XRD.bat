@echo off
chcp 65001 >nul
setlocal EnableExtensions

rem CrystalShift XRD - double-click launcher (Windows)
cd /d "%~dp0"

set "PORT=8508"
set "URL=http://localhost:%PORT%/"
set "VENV_PY=%~dp0.venv\Scripts\python.exe"
set "VENV_STREAMLIT=%~dp0.venv\Scripts\streamlit.exe"

echo ============================================
echo   CrystalShift XRD
echo   工作目录: %CD%
echo ============================================
echo.

rem Prefer project virtual environment
if exist "%VENV_PY%" goto :have_venv

echo [1/3] 未找到 .venv，正在创建虚拟环境...
call :find_python
if errorlevel 1 (
    echo.
    echo 错误: 未找到 Python 3.11+。
    echo 请先安装 Python，并确保 py 或 python 在 PATH 中。
    echo 下载: https://www.python.org/downloads/
    goto :fail
)
echo 使用解释器: %PYTHON_CMD%
%PYTHON_CMD% -m venv .venv
if errorlevel 1 (
    echo 错误: 创建虚拟环境失败。
    goto :fail
)

:have_venv
if not exist "%VENV_PY%" (
    echo 错误: 虚拟环境不完整，缺少 .venv\Scripts\python.exe
    goto :fail
)

echo [2/3] 检查依赖...
"%VENV_PY%" -c "import streamlit, numpy, plotly, pymatgen" 1>nul 2>nul
if errorlevel 1 (
    echo 正在安装运行依赖（首次可能需要几分钟）...
    "%VENV_PY%" -m pip install --upgrade pip
    if errorlevel 1 goto :fail
    "%VENV_PY%" -m pip install -e .
    if errorlevel 1 (
        echo 错误: 依赖安装失败。
        goto :fail
    )
) else (
    echo 依赖已就绪。
)

echo.
echo [3/3] 启动 Streamlit 服务...
echo 浏览器地址: %URL%
echo 关闭本窗口即可停止服务。
echo.

rem Open browser shortly after server starts
start "" cmd /c "timeout /t 2 /nobreak >nul & start "" "%URL%""

"%VENV_PY%" -m streamlit run app.py --server.port %PORT% --server.headless true
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" (
    echo Streamlit 已退出，代码: %EXIT_CODE%
    pause
)
endlocal
exit /b %EXIT_CODE%

:find_python
set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -c "import sys" 1>nul 2>nul && set "PYTHON_CMD=py -3.12" && exit /b 0
    py -3.11 -c "import sys" 1>nul 2>nul && set "PYTHON_CMD=py -3.11" && exit /b 0
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 1>nul 2>nul && set "PYTHON_CMD=py -3" && exit /b 0
)
where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 1>nul 2>nul && set "PYTHON_CMD=python" && exit /b 0
)
exit /b 1

:fail
echo.
pause
endlocal
exit /b 1

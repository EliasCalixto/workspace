@echo off
setlocal
title Autologin BMS

rem Carpeta del proyecto (relativa a tu home de Windows)
set "SCRIPT_DIR=%USERPROFILE%\Dev\Workspace\autologin_windows"

if not exist "%SCRIPT_DIR%\autologin.py" (
    echo No se encontro "%SCRIPT_DIR%\autologin.py"
    pause
    exit /b 1
)

pushd "%SCRIPT_DIR%"

rem Usa el lanzador "py" si existe; si no, "python"
where py >nul 2>&1
if %errorlevel%==0 (
    py autologin.py %*
) else (
    python autologin.py %*
)

set "EXITCODE=%errorlevel%"
popd

if not "%EXITCODE%"=="0" (
    echo.
    echo autologin.py termino con codigo %EXITCODE%
    pause
)
exit /b %EXITCODE%

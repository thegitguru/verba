@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  VERBA BUILD SYSTEM  |  Enterprise Build Pipeline
::  Builds a standalone verba.exe via PyInstaller
:: ============================================================

title Verba Build System

:: ── Enable ANSI/VT100 color support (Windows 10 1511+) ──────
reg query "HKCU\Console" /v VirtualTerminalLevel >nul 2>&1
if errorlevel 1 (
    reg add "HKCU\Console" /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1
)

set "ESC="
for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RESET=%ESC%[0m"
set "BOLD=%ESC%[1m"
set "DIM=%ESC%[2m"
set "CYAN=%ESC%[36m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "RED=%ESC%[31m"
set "WHITE=%ESC%[97m"
set "GREY=%ESC%[90m"

:: ── Build metadata ──────────────────────────────────────────
set "BUILD_VERSION=1.0.0"
set "PRODUCT_NAME=Verba"
set "SPEC_FILE=verba.spec"
set "OUTPUT_BINARY=dist\verba.exe"

:: Optional: files to bundle alongside the binary in the release zip
:: Add paths separated by spaces, e.g. README.md LICENSE CHANGELOG.md
set "RELEASE_EXTRAS=README.md LICENSE CHANGELOG.md"

:: Build a timestamped log filename (YYYYMMDD_HHMMSS)
set "_D=%date:~-4,4%%date:~-7,2%%date:~-10,2%"
set "_T=%time:~0,2%%time:~3,2%%time:~6,2%"
set "_T=!_T: =0!"
set "LOG_FILE=build\logs\build_!_D!_!_T!.log"

:: Release artefact paths
set "RELEASE_DIR=release"
set "RELEASE_NAME=verba-v%BUILD_VERSION%-win64"
set "RELEASE_STAGING=%RELEASE_DIR%\!RELEASE_NAME!"
set "RELEASE_ZIP=%RELEASE_DIR%\!RELEASE_NAME!.zip"

set "EXIT_CODE=0"

:: ── Setup ────────────────────────────────────────────────────
cls
call :fn_header

if not exist "build\logs" mkdir "build\logs" >nul 2>&1
call :fn_log_init

:: ── Pre-flight checks ────────────────────────────────────────
call :fn_phase "PRE-FLIGHT" "Validating build environment"

call :fn_check_tool "python" "--version" "Python runtime"
if !errorlevel! neq 0 goto :err_abort

call :fn_check_tool "pyinstaller" "--version" "PyInstaller"
if !errorlevel! neq 0 goto :err_abort

call :fn_check_file "%SPEC_FILE%" "Build spec"
if !errorlevel! neq 0 goto :err_abort

call :fn_ok "All pre-flight checks passed"
echo.

:: ── Environment info ─────────────────────────────────────────
call :fn_phase "ENVIRONMENT" "Collecting system info"

for /f "tokens=*" %%v in ('python --version 2^>^&1')      do set "PY_VER=%%v"
for /f "tokens=*" %%v in ('pyinstaller --version 2^>^&1') do set "PI_VER=%%v"

call :fn_kv "Python"       "!PY_VER!"
call :fn_kv "PyInstaller"  "!PI_VER!"
call :fn_kv "Spec file"    "%SPEC_FILE%"
call :fn_kv "Target"       "%OUTPUT_BINARY%"
call :fn_kv "Release zip"  "%RELEASE_ZIP%"
call :fn_kv "Build log"    "%LOG_FILE%"
echo.

:: ── Clean ────────────────────────────────────────────────────
call :fn_phase "CLEAN" "Removing previous build artefacts"

if exist "build" (
    call :fn_step "Purging build\ ..."
    rd /s /q build >nul 2>&1
    call :fn_ok  "build\ removed"
)
if exist "dist" (
    call :fn_step "Purging dist\ ..."
    rd /s /q dist >nul 2>&1
    call :fn_ok  "dist\ removed"
)
if exist "%RELEASE_STAGING%" (
    call :fn_step "Purging previous staging dir ..."
    rd /s /q "%RELEASE_STAGING%" >nul 2>&1
    call :fn_ok  "Staging dir cleared"
)

if not exist "build\logs" mkdir "build\logs" >nul 2>&1
echo.

:: ── Compile ──────────────────────────────────────────────────
call :fn_phase "COMPILE" "Running PyInstaller"
call :fn_step  "Invoking: pyinstaller %SPEC_FILE% --clean"
echo.

pyinstaller "%SPEC_FILE%" --clean >> "%LOG_FILE%" 2>&1
set "PI_EXIT=!errorlevel!"

echo.
if !PI_EXIT! neq 0 (
    call :fn_error "PyInstaller failed  (exit code !PI_EXIT!)"
    call :fn_error "Full trace:  %LOG_FILE%"
    set "EXIT_CODE=!PI_EXIT!"
    goto :err_abort
)

call :fn_ok "Compilation successful"
echo.

:: ── Post-build validation ────────────────────────────────────
call :fn_phase "VALIDATE" "Verifying output binary"

call :fn_check_file "%OUTPUT_BINARY%" "Output binary"
if !errorlevel! neq 0 (
    call :fn_error "Binary missing at expected path"
    set "EXIT_CODE=1"
    goto :err_abort
)

for %%f in ("%OUTPUT_BINARY%") do set "BINARY_SIZE=%%~zf"
set /a "BINARY_SIZE_KB=!BINARY_SIZE! / 1024"
set /a "BINARY_SIZE_MB=!BINARY_SIZE_KB! / 1024"

call :fn_ok "Binary present and readable"
call :fn_kv  "Size" "!BINARY_SIZE_KB! KB  (!BINARY_SIZE_MB! MB)"
echo.

:: ── Package ───────────────────────────────────────────────────
call :fn_phase "PACKAGE" "Creating release zip"

:: Wipe and recreate staging folder
if exist "%RELEASE_STAGING%" rd /s /q "%RELEASE_STAGING%" >nul 2>&1
mkdir "%RELEASE_STAGING%" >nul 2>&1
call :fn_ok  "Staging dir ready: %RELEASE_STAGING%"

:: Copy binary
call :fn_step "Copying verba.exe ..."
copy /y "%OUTPUT_BINARY%" "%RELEASE_STAGING%\verba.exe" >nul 2>&1
if !errorlevel! neq 0 (
    call :fn_error "Failed to copy binary into staging"
    set "EXIT_CODE=1"
    goto :err_abort
)
call :fn_ok "verba.exe staged"

:: Copy optional extras if they exist
for %%X in (%RELEASE_EXTRAS%) do (
    if exist "%%X" (
        call :fn_step "Staging %%X ..."
        copy /y "%%X" "%RELEASE_STAGING%\%%X" >nul 2>&1
        call :fn_ok "%%X staged"
    ) else (
        call :fn_step "Skipping %%X  (not found)"
    )
)

:: Write a minimal RELEASE_INFO.txt into the zip
(
    echo Verba v%BUILD_VERSION% — Windows x64
    echo Built : %DATE% %TIME%
    echo.
    echo https://github.com/yourname/verba
) > "%RELEASE_STAGING%\RELEASE_INFO.txt"
call :fn_ok "RELEASE_INFO.txt written"

:: Remove any previous zip with the same name
if exist "%RELEASE_ZIP%" del /f /q "%RELEASE_ZIP%" >nul 2>&1

:: Use PowerShell Compress-Archive (available Windows 8.1+)
call :fn_step "Compressing to %RELEASE_ZIP% ..."
powershell -NoProfile -Command ^
    "Compress-Archive -Path '%RELEASE_STAGING%\*' -DestinationPath '%RELEASE_ZIP%' -Force" ^
    >> "%LOG_FILE%" 2>&1
if !errorlevel! neq 0 (
    call :fn_error "Compression failed — check PowerShell availability"
    set "EXIT_CODE=1"
    goto :err_abort
)

for %%f in ("%RELEASE_ZIP%") do set "ZIP_SIZE=%%~zf"
set /a "ZIP_SIZE_KB=!ZIP_SIZE! / 1024"
set /a "ZIP_SIZE_MB=!ZIP_SIZE_KB! / 1024"

call :fn_ok "Release zip created"
call :fn_kv  "Archive" "%RELEASE_ZIP%"
call :fn_kv  "Zip size" "!ZIP_SIZE_KB! KB  (!ZIP_SIZE_MB! MB)"
echo.

:: ── Done ─────────────────────────────────────────────────────
call :fn_summary_ok
goto :end

:: ════════════════════════════════════════════════════════════
::  ERROR HANDLER
:: ════════════════════════════════════════════════════════════
:err_abort
call :fn_summary_fail
goto :end

:: ════════════════════════════════════════════════════════════
::  HELPER FUNCTIONS
:: ════════════════════════════════════════════════════════════

:fn_header
echo.
echo %BOLD%%CYAN%  +------------------------------------------------------+%RESET%
echo %BOLD%%CYAN%  ^|       V E R B A   B U I L D   S Y S T E M          ^|%RESET%
echo %BOLD%%CYAN%  ^|                                                      ^|%RESET%
echo %BOLD%%CYAN%  ^|%RESET%  %WHITE%v%BUILD_VERSION%%RESET%            %GREY%Enterprise Build Pipeline%RESET%          %BOLD%%CYAN%^|%RESET%
echo %BOLD%%CYAN%  ^|%RESET%  %GREY%PRE-FLIGHT · ENV · CLEAN · COMPILE · VALIDATE · PACKAGE%RESET%  %BOLD%%CYAN%^|%RESET%
echo %BOLD%%CYAN%  +------------------------------------------------------+%RESET%
echo.
exit /b 0

:fn_phase
echo %BOLD%%WHITE%  [ %~1 ]%RESET%  %GREY%%~2%RESET%
exit /b 0

:fn_step
echo %GREY%      *  %~1%RESET%
exit /b 0

:fn_ok
echo %GREEN%      +  %~1%RESET%
exit /b 0

:fn_error
echo %RED%      !  %~1%RESET%
exit /b 0

:fn_kv
echo %GREY%         %-16s%RESET%  %WHITE%%~2%RESET%
exit /b 0

:fn_check_tool
set "_TOOL=%~1"
set "_FLAG=%~2"
set "_LABEL=%~3"
call :fn_step "Checking %_LABEL% ..."
%_TOOL% %_FLAG% >nul 2>&1
if !errorlevel! neq 0 (
    call :fn_error "%_LABEL% not found — is '%_TOOL%' on PATH?"
    exit /b 1
)
call :fn_ok "%_LABEL% OK"
exit /b 0

:fn_check_file
set "_FPATH=%~1"
set "_FLABEL=%~2"
call :fn_step "Checking %_FLABEL% (%_FPATH%) ..."
if not exist "%_FPATH%" (
    call :fn_error "%_FLABEL% not found: %_FPATH%"
    exit /b 1
)
call :fn_ok "%_FLABEL% found"
exit /b 0

:fn_log_init
(
    echo Verba Build Log
    echo Started : %DATE% %TIME%
    echo ========================================
) > "%LOG_FILE%"
exit /b 0

:fn_summary_ok
echo.
echo %BOLD%%GREEN%  +------------------------------------------------------+%RESET%
echo %BOLD%%GREEN%  ^|                  BUILD SUCCEEDED                    ^|%RESET%
echo %BOLD%%GREEN%  +------------------------------------------------------+%RESET%
echo.
echo %WHITE%  Binary   %RESET%  %BOLD%%OUTPUT_BINARY%%RESET%
echo %WHITE%  Size     %RESET%  %BOLD%!BINARY_SIZE_KB! KB  (!BINARY_SIZE_MB! MB)%RESET%
echo %WHITE%  Release  %RESET%  %BOLD%%RELEASE_ZIP%%RESET%
echo %WHITE%  Zip size %RESET%  %BOLD%!ZIP_SIZE_KB! KB  (!ZIP_SIZE_MB! MB)%RESET%
echo %WHITE%  Log      %RESET%  %GREY%%LOG_FILE%%RESET%
echo.
echo %GREY%  Run:     .\dist\verba.exe --help%RESET%
echo %GREY%  Ship:    %RELEASE_ZIP%%RESET%
echo.
pause
exit /b 0

:fn_summary_fail
echo.
echo %BOLD%%RED%  +------------------------------------------------------+%RESET%
echo %BOLD%%RED%  ^|                   BUILD FAILED                      ^|%RESET%
echo %BOLD%%RED%  +------------------------------------------------------+%RESET%
echo.
echo %WHITE%  Exit code  %RESET%  %RED%%EXIT_CODE%%RESET%
echo %WHITE%  Log        %RESET%  %GREY%%LOG_FILE%%RESET%
echo.
echo %YELLOW%  Inspect the build log for the full PyInstaller trace.%RESET%
echo.
pause
exit /b 0

:end
endlocal
exit /b %EXIT_CODE%
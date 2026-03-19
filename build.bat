@echo off
echo Building verba.exe...
pyinstaller verba.spec --clean
echo.
echo Done. Standalone binary: dist\verba.exe

@echo off
REM GlobeTrotter — Build Executable
REM Run this file from the project root:  build.bat

echo ==============================================
echo  GlobeTrotter Build Script
echo ==============================================

echo [1/3] Installing / upgrading PyInstaller...
pip install --upgrade pyinstaller --quiet

echo [2/3] Building executable...
pyinstaller GlobeTrotter.spec --clean --noconfirm

echo [3/3] Done!
echo.
echo Output folder:  dist\GlobeTrotter\
echo Run it with:    dist\GlobeTrotter\GlobeTrotter.exe
echo.
echo Share the entire  dist\GlobeTrotter\  folder with users.
echo (They do NOT need Python installed.)
pause

@echo off
echo ================================
echo GlassCAD - Windows Build Script
echo ================================
echo.

echo [1/4] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11 from python.org first,
    echo and make sure "Add python.exe to PATH" was checked during install.
    pause
    exit /b 1
)

echo.
echo [2/4] Installing dependencies (this takes a few minutes)...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [3/4] Building GlassCAD.exe and GlassCAD-Hologram.exe...
pyinstaller windows.spec

echo.
echo [4/4] Build complete!
echo.
echo Your application is in the "dist" folder.
echo Look for: dist\GlassCAD\GlassCAD.exe
echo.
echo Double-click GlassCAD.exe to run the app.
echo (Do not move GlassCAD.exe out of its folder - it needs the
echo  other files sitting next to it, including GlassCAD-Hologram.exe)
echo.
pause

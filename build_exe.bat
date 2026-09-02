@echo off
echo ===================================================
echo   Building DEA MultiPageStoryReader.exe
echo   Developed by DEA Innovations (www.deainnovations.com)
echo ===================================================
echo.

echo 1. Generating App Icons...
python generate_icon.py

echo.
echo 2. Running PyInstaller Build...
pyinstaller --clean article_reader.spec

echo.
if exist "dist\MultiPageStoryReader.exe" (
    echo ===================================================
    echo   BUILD SUCCESSFUL!
    echo   Executable is ready at: dist\MultiPageStoryReader.exe
    echo ===================================================
) else (
    echo [ERROR] Build failed. Please check the logs above.
)
pause

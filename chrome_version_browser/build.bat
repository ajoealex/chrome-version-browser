@echo off
pip install -r requirements.txt
python -m PyInstaller --onefile --console --name run main.py
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

set "PKG=dist\chrome_version_browser"
if exist "%PKG%" rmdir /s /q "%PKG%"
mkdir "%PKG%"

move /y dist\run.exe "%PKG%\run.exe" >nul

if exist app_data (
    xcopy app_data "%PKG%\app_data" /E /I /Y >nul
) else (
    mkdir "%PKG%\app_data"
)

copy /y app.properties "%PKG%\app.properties" >nul
copy /y README.md "%PKG%\README.md" >nul

echo Build complete. See dist\chrome_version_browser\run.exe

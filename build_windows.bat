@echo off
setlocal
cd /d "%~dp0"

echo Installing dependencies...
python -m pip install -r requirements.txt -r requirements-build.txt
if errorlevel 1 exit /b 1

echo Building MyNotes.exe...
python -m PyInstaller --noconfirm --clean --windowed --onefile --name MyNotes main.py
if errorlevel 1 exit /b 1

echo.
echo Done. Executable: dist\MyNotes.exe
echo Double-click dist\MyNotes.exe to run (no Python install needed).
endlocal

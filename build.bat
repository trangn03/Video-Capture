@echo off
echo Deleting old versions...
rd /s /q build
rd /s /q dist
echo Activate virtual environment
call venv/Scripts/activate
echo Building new EXE...
pyinstaller --onefile --windowed capture.py
echo Done! Your new app is in the "dist" folder.
pause
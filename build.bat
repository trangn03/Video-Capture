@echo off
echo Deleting old versions...
rd /s /q build
rd /s /q dist
echo Building new EXE...
pyinstaller --onefile --windowed capture.py
echo Done! Your new app is in the "dist" folder.
pause
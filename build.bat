@echo off
echo [1/4] Deleting old versions...
rd /s /q build
rd /s /q dist
echo [2/4] Activating Virtual Environment...
call venv\Scripts\activate

echo [3/4] Installing requirements inside venv...
pip install opencv-python pyinstaller

echo [4/4] Creating the file..
pyinstaller --onefile --console capture.py

echo DONE! 
echo Your file is ready.
pause
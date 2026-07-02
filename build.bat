@echo off
echo [1/5] Deleting old versions...
rd /s /q build
rd /s /q dist

echo [2/5] Activating Virtual Environment...
call venv\Scripts\activate

echo [3/5] Upgrading pip to the latest version...
python -m pip install --upgrade pip

echo [4/5] Installing requirements inside venv...
pip install opencv-python pyinstaller

echo [5/5] Creating the file...
pyinstaller --onefile --console capture.py

echo DONE! 
echo Your file is ready.
pause
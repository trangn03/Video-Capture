# Video Capture

A tool for capturing images from one or more connected cameras simultaneously. Designed for manufacturing/inspection workflows where photos need to be organized by part number and job number.

## Features

- Detects all connected cameras (up to 10)
- Displays live feeds from all cameras side-by-side in a single window
- Captures from every camera at once with a single keypress
- Organizes saved images into folders by part number and job number
- Resumes numbering from where it left off if a session is interrupted

## Requirements

- Python 3.x
- Dependencies listed in [requirements.txt](requirements.txt):

  - `opencv-python`
  - `numpy`

## Installation

```bash
pip install -r requirements.txt
```

## How to Run

```bash
python capture.py
```

You will be prompted to enter:

- **Part Number** — used to name the top-level folder (defaults to `UNKNOWN`)
- **Job Number** — used to name the subfolder (defaults to `TEMP`)

Images are saved to: `<PART_NUMBER>/JOB_<JOB_NUMBER>/`

### Controls

| Key     | Action                            |
|---------|-----------------------------------|
| `SPACE` | Capture a photo from all cameras  |
| `R`     | Retake (discard the last capture) |
| `ESC`   | Quit                              |

## Output

Each capture set saves one image per camera:

```text
PART_<part_number>/
└── JOB_<job_number>/
    ├── PART_<part_number>_CAM0_1.jpg
    ├── PART_<part_number>_CAM1_1.jpg
    ├── PART_<part_number>_CAM0_2.jpg
    └── ...
```

If images already exist in the folder, the counter picks up from the last image so existing files are never overwritten.

## Building a Standalone Executable (Windows)

A [build.bat](build.bat) script is included to package the app into a single `.exe` using PyInstaller.

```bat
build.bat
```

The finished executable will be output to `dist\capture.exe`. No Python installation is required to run it.

> The script expects a `venv` virtual environment in the project root. Create one first with `python -m venv venv`.

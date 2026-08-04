# Video Capture

A tool for capturing images from one or more connected cameras simultaneously. Designed for manufacturing/inspection workflows where photos need to be organized by part number and job number.

## Features

- Detects all connected cameras (up to 10)
- Displays live feeds from all cameras side-by-side in a single window
- Captures from every camera at once with a single keypress
- Optional GUI ([capture_gui.py](capture_gui.py)) for entering part number, job number, and serial numbers without a terminal
- Organizes saved images into folders by part number, job number, and serial number (or quantity, if no serial numbers are used)
- Resumes numbering from where it left off if a session is interrupted
- On-screen status banner (capture complete, retake, etc.) shown in the camera window itself, so status is visible even when run from the GUI build with no console

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
- **Job Number** — used to name the job subfolder (defaults to `TEMP`)
- **Serial Numbers** — one per line, ENTER on a blank line to finish (optional — leave blank to capture by quantity instead)

Or run the GUI instead, which collects the same inputs from a window instead of the terminal:

```bash
python capture_gui.py
```

### Controls

| Key     | Action                            |
|---------|-----------------------------------|
| `SPACE` | Capture a photo from all cameras  |
| `R`     | Retake (discard the last capture) |
| `ESC`   | Quit (press again to confirm)     |

Status messages (capture complete, retake, queue finished, etc.) are shown both in the console and as a temporary banner across the bottom of the camera window, so they're visible even when running the GUI build with no console attached.

## Output

Each capture set saves one image per camera. Images are grouped into their own subfolder so you can jump straight to one serial number or quantity without scanning the whole job folder:

**With serial numbers** — one folder per SN, under `SN_<serial>/`:

```text
PART_<part_number>/
└── JOB_<job_number>/
    ├── SN_ABC123/
    │   ├── PART_<part_number>_CAM0_SNABC123_1.jpg
    │   └── PART_<part_number>_CAM1_SNABC123_1.jpg
    └── SN_ABC124/
        ├── PART_<part_number>_CAM0_SNABC124_1.jpg
        └── PART_<part_number>_CAM1_SNABC124_1.jpg
```

**Without serial numbers** — one folder per quantity, under `SET_<n>/`:

```text
PART_<part_number>/
└── JOB_<job_number>/
    ├── SET_1/
    │   ├── PART_<part_number>_CAM0_1.jpg
    │   └── PART_<part_number>_CAM1_1.jpg
    └── SET_2/
        ├── PART_<part_number>_CAM0_1.jpg
        └── PART_<part_number>_CAM1_1.jpg
```

If images already exist in a folder, the counter picks up from the last image so existing files are never overwritten.

## Building a Standalone Executable (Windows)

A [build.bat](build.bat) script is included to package the app into a single `.exe` using PyInstaller.

```bat
build.bat
```

The finished executable will be output to `dist\capture.exe`. No Python installation is required to run it.

> The script expects a `venv` virtual environment in the project root. Create one first with `python -m venv venv`.

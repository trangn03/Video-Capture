"""
main.py — Simulates the terminal output of capture.py without needing real cameras.
Run this to preview what the session flow looks like end to end.
"""

import time

def simulate(text, delay=0.03):
    """Print text character by character to mimic live terminal output."""
    for ch in text:
        print(ch, end='', flush=True)
        time.sleep(delay)
    print()

def section(title):
    print()
    simulate(f"{'=' * 40}")
    simulate(f"  {title}")
    simulate(f"{'=' * 40}")

def run():
    section("STARTUP")
    simulate("Capture begin...This may take a moment")
    time.sleep(0.5)
    simulate("Camera 0 ... connected.")
    time.sleep(0.3)
    simulate("Camera 1 ... connected.")
    time.sleep(0.3)
    simulate("There are 2 available camera(s) ready to take picture")

    section("SESSION INFO")
    simulate("Enter PART NUMBER: ", delay=0.02)
    time.sleep(0.4)
    simulate("ABC123", delay=0.07)

    simulate("Enter JOB NUMBER: ", delay=0.02)
    time.sleep(0.3)
    simulate("42", delay=0.07)

    time.sleep(0.3)
    simulate("Created folder: ABC123/JOB_42")
    simulate(" Saving to: C:\\Users\\User\\Downloads\\Video-Capture\\ABC123\\JOB_42")

    section("SERIAL NUMBER QUEUE")
    simulate("Enter serial numbers one per line. Use ENTER again when done:")
    time.sleep(0.3)
    simulate("  SN 1: ", delay=0.02)
    time.sleep(0.4)
    simulate("SN001", delay=0.07)
    simulate("  SN 2: ", delay=0.02)
    time.sleep(0.4)
    simulate("SN002", delay=0.07)
    simulate("  SN 3: ", delay=0.02)
    time.sleep(0.4)
    simulate("SN003", delay=0.07)
    simulate("  SN 4: ", delay=0.02)
    time.sleep(0.3)
    simulate("(blank — done)")
    time.sleep(0.2)
    simulate("3 serial number(s) queued.")

    section("CAPTURE SESSION")
    simulate("[SPACE] to Capture | [R] to Retake Last | [ESC] to Quit")
    simulate("[ camera window opens — SN: SN001  (1 of 3) shown on feed ]")
    time.sleep(1.0)

    simulate("\n--- Capture set 1 | SN: SN001 complete ---")
    time.sleep(0.6)
    simulate("[ camera feed advances — SN: SN002  (2 of 3) ]")
    time.sleep(1.0)

    simulate("\n--- Capture set 2 | SN: SN002 complete ---")
    time.sleep(0.6)
    simulate("[ camera feed advances — SN: SN003  (3 of 3) ]")
    time.sleep(1.0)

    simulate("\n--- Capture set 3 | SN: SN003 complete ---")
    time.sleep(0.4)
    simulate("All serial numbers captured. Press R to retake the last set or ESC to finish.")
    time.sleep(1.0)
    simulate("[ ESC pressed — session ends ]")

    section("SESSION SUMMARY")
    simulate("=" * 40)
    simulate("         SESSION SUMMARY")
    simulate("=" * 40)
    simulate("  Part Number : ABC123")
    simulate("  Job Number  : 42")
    simulate("  Capture Sets: 3")
    simulate("  Images Saved: 6")
    simulate("  SNs Captured: SN001, SN002, SN003")
    simulate("  Saved To    : C:\\Users\\User\\Downloads\\Video-Capture\\ABC123\\JOB_42")
    simulate("=" * 40)

    section("FILES CREATED")
    files = [
        "ABC123/JOB_42/PART_ABC123_CAM0_SNSN001_1.jpg",
        "ABC123/JOB_42/PART_ABC123_CAM1_SNSN001_1.jpg",
        "ABC123/JOB_42/PART_ABC123_CAM0_SNSN002_2.jpg",
        "ABC123/JOB_42/PART_ABC123_CAM1_SNSN002_2.jpg",
        "ABC123/JOB_42/PART_ABC123_CAM0_SNSN003_3.jpg",
        "ABC123/JOB_42/PART_ABC123_CAM1_SNSN003_3.jpg",
    ]
    for f in files:
        simulate(f"  {f}", delay=0.01)
        time.sleep(0.1)

    print()
    simulate("Done. Press ENTER to close.")
    input()

if __name__ == "__main__":
    run()

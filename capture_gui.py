import tkinter as tk
from tkinter import messagebox, font
import threading
import capture

class CaptureGUI:
    def __init__(self):
        # Window set up
        self.root = tk.Tk()
        self.root.title("Capture Dashboard")
        self.root.geometry("560x650")
        
        # State
        self.detected_cameras = []
        self.is_detecting_cameras = False

        # Create custom font objects
        text_font = font.Font(family="Segoe UI", size=14)
        bold_font = font.Font(family="Segoe UI", size=14, weight="bold")
        small_font = font.Font(family="Segoe UI", size=10)
        status_font = font.Font(family="Segoe UI", size=11)
        
        # Camera Detection Section
        self.frame_camera = tk.LabelFrame(
            self.root,
            text=" Camera Status ",
            font=bold_font,
            padx=12,
            pady=8,
        )
        self.frame_camera.pack(fill="x", padx=18, pady=(12, 6))

        # Top row inside camera frame: status + refresh button
        self.frame_cam_top = tk.Frame(self.frame_camera)
        self.frame_cam_top.pack(fill="x")

        self.label_cam_status = tk.Label(
            self.frame_cam_top,
            text="Detecting cameras...",
            font=status_font,
            fg="#555555",
            anchor="w",
        )
        self.label_cam_status.pack(side="left", fill="x", expand=True)

        self.btn_refresh = tk.Button(
            self.frame_cam_top,
            text="Refresh",
            font=small_font,
            command=self.refresh_cameras,
            padx=8,
            pady=2,
        )
        self.btn_refresh.pack(side="right")

        self.label_cam_details = tk.Label(
            self.frame_camera,
            text="",
            font=small_font,
            fg="#444444",
            anchor="w",
            justify="left",
        )
        self.label_cam_details.pack(fill="x", pady=(4, 0))

        # Entering part number
        self.label_part = tk.Label(self.root, text="Enter PART NUMBER:", font=text_font)
        self.label_part.pack(padx=10, pady=(10, 2))
        
        self.entry_part = tk.Entry(self.root, font=text_font, justify="center")
        self.entry_part.pack(padx=10, pady=(0, 10))
        
        # Entering job number 
        self.label_job = tk.Label(self.root, text="Enter JOB NUMBER:", font=text_font)
        self.label_job.pack(padx=10, pady=(5, 2))
        
        self.entry_job = tk.Entry(self.root, font=text_font, justify="center")
        self.entry_job.pack(padx=10, pady=(0, 10))
        
        # Entering serial number
        self.label_sn = tk.Label(self.root, text="Enter SERIAL NUMBERS (one per line):", font=text_font)
        self.label_sn.pack(padx=10, pady=(5, 2))
        
        self.text_sn = tk.Text(self.root, height=4, width=32, font=text_font)
        self.text_sn.pack(padx=10, pady=(0, 0))
        # Update the counter each time the operator types in the serial box
        self.text_sn.bind("<KeyRelease>", self.update_sn_counter)

        # Live count of how many serial numbers are currently entered
        self.label_sn_count = tk.Label(self.root, text="0 serial number(s) entered",
                                       font=small_font)
        self.label_sn_count.pack(padx=10, pady=(2, 8))

        # Start the capture button
        self.btn_start = tk.Button(
            self.root,
            text="Start Capture",
            font=bold_font,
            bg="#4CAF50",
            fg="black",
            command=self.on_start,   # run on_start() when clicked
            padx=16,
            pady=6,
        )
        self.btn_start.pack(padx=10, pady=(5, 12))

        # Initial camera scan on launch
        self.refresh_cameras()

        self.root.mainloop()

    def refresh_cameras(self):
        """Starts asynchronous camera detection in a background thread."""
        if self.is_detecting_cameras:
            return
        
        self.is_detecting_cameras = True
        self.btn_refresh.config(state="disabled")
        self.label_cam_status.config(
            text="Scanning camera devices... (please wait)",
            fg="#0055A5",
        )
        self.label_cam_details.config(text="")

        thread = threading.Thread(target=self._detect_cameras_worker, daemon=True)
        thread.start()

    def _detect_cameras_worker(self):
        """Worker thread to probe cameras without blocking the GUI."""
        cameras = capture.probe_cameras(max_index=10)
        # Safely update GUI in main thread
        self.root.after(0, self._apply_camera_results, cameras)

    def _apply_camera_results(self, cameras):
        """Updates GUI widgets with probe results."""
        self.detected_cameras = cameras
        self.is_detecting_cameras = False
        self.btn_refresh.config(state="normal")

        count = len(cameras)
        if count > 0:
            self.label_cam_status.config(
                text=f"{count} camera(s) ready",
                fg="#2E7D32",  # Green
            )
            details = "\n".join(
                f"• Camera {cam['id']}: {cam['width']}x{cam['height']}"
                for cam in cameras
            )
            self.label_cam_details.config(text=details, fg="#2E7D32")
        else:
            self.label_cam_status.config(
                text="No cameras detected",
                fg="#C62828",  # Red
            )
            self.label_cam_details.config(
                text="Please connect your camera(s) and click 'Refresh'.",
                fg="#C62828",
            )

    def update_sn_counter(self, event=None):
        # Show a running total of how many serial numbers are entered
        raw = self.text_sn.get("1.0", "end")   # everything typed in the box

        # Count each line that actually has text, skipping blank lines
        count = 0
        for line in raw.splitlines():
            if line.strip():   # line has something other than spaces
                count += 1

        self.label_sn_count.config(text=f"{count} serial number(s) entered")

    def on_start(self):
        if self.is_detecting_cameras:
            messagebox.showinfo(
                "Detecting cameras",
                "Camera scan is in progress. Please wait a moment for detection to complete.",
            )
            return

        if not self.detected_cameras:
            proceed = messagebox.askyesno(
                "No Cameras Detected",
                "No cameras were detected during the scan.\n\nDo you still want to attempt starting capture?",
            )
            if not proceed:
                return

        # 1. Read the values the operator typed into the GUI
        part_number = self.entry_part.get().strip()
        job_number = self.entry_job.get().strip()

        # The serial-number box is a multi-line Text widget. "1.0" = line 1, char 0;
        # "end" = the very end. Grab everything, then trim the outer whitespace.
        raw_sns = self.text_sn.get("1.0", "end").strip()

        # Split that block into individual lines, clean each one, and skip blanks.
        serial_numbers = []
        for line in raw_sns.splitlines():
            cleaned = line.strip()   # remove stray spaces around this serial number
            if cleaned:              # empty string is falsy -> skip blank lines
                serial_numbers.append(cleaned)

        # 2. Basic validation so we don't start a session with empty IDs
        if not part_number:
            messagebox.showerror("Missing info", "Please enter a PART NUMBER.")
            return
        if not job_number:
            messagebox.showerror("Missing info", "Please enter a JOB NUMBER.")
            return

        # Flag duplicate serial numbers so the operator can fix them before
        # capture starts (capture.py would otherwise dedupe them silently).
        seen_sns = set()
        duplicate_sns = []
        for sn in serial_numbers:
            if sn in seen_sns and sn not in duplicate_sns:
                duplicate_sns.append(sn)
            seen_sns.add(sn)
        if duplicate_sns:
            messagebox.showerror(
                "Duplicate serial number(s)",
                "The following serial number(s) were entered more than once:\n\n"
                + "\n".join(duplicate_sns)
                + "\n\nPlease remove the duplicate(s) and try again.",
            )
            return

        # 3. Hide the GUI while the OpenCV capture window runs on the main thread,
        #    then bring the GUI back once the session ends (ESC / window closed).
        self.root.withdraw()
        try:
            capture.start_capture(
                part_number=part_number,
                job_number=job_number,
                serial_numbers=serial_numbers,
            )
        except Exception as e:
            messagebox.showerror("Capture error", str(e))
        finally:
            self.root.destroy()


if __name__ == "__main__":
    CaptureGUI()


"""
capture_gui.py 

This module provides a graphical user interface (GUI) built with Tkinter for configuring
and starting multi-camera image capture sessions without relying on terminal prompts.

Features:
    - Pre-flight Camera Status indicator with real-time detection & refresh.
    - Input fields for Part Number and Job Number.
    - Multi-line Serial Number entry with live counter and duplicate detection.
    - Seamless handoff to the OpenCV multi-camera capture window (capture.py).
    - Automatic dashboard restoration when the capture session ends.
"""

import tkinter as tk
from tkinter import messagebox, font, ttk
import threading
import capture


class CaptureGUI:
    """
    Tkinter desktop application for configuring and initiating multi-camera capture sessions.

    Collects job metadata (part number, job number, and queued serial numbers), performs
    input validation, checks camera connectivity, and launches the OpenCV capture session.
    """

    def __init__(self):
        """
        Initialize the dashboard window, layout components, fonts, input widgets,
        and start an asynchronous pre-flight camera check.
        """
        # Window setup
        self.root = tk.Tk()
        self.root.title("Capture Dashboard")
        self.root.geometry("560x660")
        self.root.minsize(500, 600)
        
        # State
        self.detected_cameras = []
        self.is_checking_cameras = False

        # Fonts
        self.font_title = font.Font(family="Segoe UI", size=14, weight="bold")
        self.font_label = font.Font(family="Segoe UI", size=12, weight="bold")
        self.font_entry = font.Font(family="Segoe UI", size=13)
        self.font_small = font.Font(family="Segoe UI", size=10)
        self.font_btn = font.Font(family="Segoe UI", size=13, weight="bold")

        # Main Container
        main_frame = tk.Frame(self.root, padx=20, pady=15)
        main_frame.pack(fill="both", expand=True)

        # -------------------------------------------------------------
        # 1. Camera Status Indicator Card
        # -------------------------------------------------------------
        self.cam_card = tk.LabelFrame(
            main_frame,
            text=" Camera Hardware Status ",
            font=self.font_small,
            padx=12,
            pady=10,
            relief="groove"
        )
        self.cam_card.pack(fill="x", pady=(0, 15))

        cam_top_row = tk.Frame(self.cam_card)
        cam_top_row.pack(fill="x")

        self.label_cam_status = tk.Label(
            cam_top_row,
            text="⏳ Checking for cameras...",
            font=self.font_label,
            anchor="w",
            fg="#555555"
        )
        self.label_cam_status.pack(side="left", fill="x", expand=True)

        self.btn_refresh_cams = tk.Button(
            cam_top_row,
            text="🔄 Refresh",
            font=self.font_small,
            command=self.check_cameras,
            padx=8,
            pady=2,
            cursor="hand2"
        )
        self.btn_refresh_cams.pack(side="right")

        self.label_cam_details = tk.Label(
            self.cam_card,
            text="Scanning camera ports...",
            font=self.font_small,
            fg="#666666",
            anchor="w",
            justify="left"
        )
        self.label_cam_details.pack(fill="x", pady=(4, 0))

        # -------------------------------------------------------------
        # 2. Input Fields: Part Number & Job Number
        # -------------------------------------------------------------
        # Part Number
        self.label_part = tk.Label(main_frame, text="PART NUMBER", font=self.font_label, anchor="w")
        self.label_part.pack(fill="x", pady=(0, 2))
        
        self.entry_part = tk.Entry(main_frame, font=self.font_entry, justify="left")
        self.entry_part.pack(fill="x", pady=(0, 10), ipady=4)
        
        # Job Number
        self.label_job = tk.Label(main_frame, text="JOB NUMBER", font=self.font_label, anchor="w")
        self.label_job.pack(fill="x", pady=(0, 2))
        
        self.entry_job = tk.Entry(main_frame, font=self.font_entry, justify="left")
        self.entry_job.pack(fill="x", pady=(0, 10), ipady=4)
        
        # -------------------------------------------------------------
        # 3. Serial Numbers Section
        # -------------------------------------------------------------
        self.label_sn = tk.Label(
            main_frame,
            text="SERIAL NUMBERS (one per line, optional):",
            font=self.font_label,
            anchor="w"
        )
        self.label_sn.pack(fill="x", pady=(0, 2))
        
        self.text_sn = tk.Text(main_frame, height=5, font=self.font_entry, relief="solid", bd=1)
        self.text_sn.pack(fill="both", expand=True, pady=(0, 2))
        self.text_sn.bind("<KeyRelease>", self.update_sn_counter)

        # Live count of entered serial numbers
        self.label_sn_count = tk.Label(
            main_frame,
            text="0 serial number(s) entered (captures will save by Set # if empty)",
            font=self.font_small,
            fg="#666666",
            anchor="w"
        )
        self.label_sn_count.pack(fill="x", pady=(0, 12))

        # -------------------------------------------------------------
        # 4. Start Capture Button
        # -------------------------------------------------------------
        self.btn_start = tk.Button(
            main_frame,
            text="▶  Start Capture Session",
            font=self.font_btn,
            bg="#2E7D32",
            fg="white",
            activebackground="#1B5E20",
            activeforeground="white",
            relief="raised",
            cursor="hand2",
            pady=10,
            command=self.on_start
        )
        self.btn_start.pack(fill="x", pady=(0, 5))

        # Trigger initial camera detection asynchronously
        self.check_cameras()

        self.root.mainloop()

    def check_cameras(self):
        """
        Probe connected cameras asynchronously in a background worker thread.

        Prevents the Tkinter UI from hanging while OpenCV scans hardware ports,
        and schedules _apply_camera_results to update the UI on the main thread.
        """
        if self.is_checking_cameras:
            return

        self.is_checking_cameras = True
        self.btn_refresh_cams.config(state="disabled", text="⏳ Checking...")
        self.label_cam_status.config(text="🔍 Detecting connected cameras...", fg="#E65100")
        self.label_cam_details.config(text="Probing video devices. Please wait...")

        def worker():
            cams = capture.detect_cameras(max_index=10)
            self.root.after(0, self._apply_camera_results, cams)

        threading.Thread(target=worker, daemon=True).start()

    def _apply_camera_results(self, cams):
        """
        Update the Camera Status card with the detection results on the main UI thread.

        Args:
            cams (list[dict]): List of detected cameras with 'id', 'width', and 'height'.
        """
        self.detected_cameras = cams
        self.is_checking_cameras = False
        self.btn_refresh_cams.config(state="normal", text="🔄 Refresh")

        if cams:
            count = len(cams)
            cam_str = f"🟢 {count} Camera{'s' if count > 1 else ''} Ready"
            self.label_cam_status.config(text=cam_str, fg="#2E7D32")
            
            # Format resolution details for each camera
            details_list = [f"• Cam {c['id']}: {c['width']}x{c['height']}" for c in cams]
            self.label_cam_details.config(
                text=" | ".join(details_list),
                fg="#333333"
            )
        else:
            self.label_cam_status.config(
                text="🔴 No Cameras Detected",
                fg="#C62828"
            )
            self.label_cam_details.config(
                text="No video device found. Please connect your camera and click Refresh.",
                fg="#C62828"
            )

    def update_sn_counter(self, event=None):
        """
        Calculate and display the running count of non-empty serial numbers entered.

        Args:
            event (tk.Event, optional): KeyRelease event triggered by typing in the Text widget.
        """
        raw = self.text_sn.get("1.0", "end")
        count = sum(1 for line in raw.splitlines() if line.strip())
        if count > 0:
            self.label_sn_count.config(
                text=f"{count} serial number(s) queued for capture",
                fg="#2E7D32"
            )
        else:
            self.label_sn_count.config(
                text="0 serial number(s) entered (captures will save by Set # if empty)",
                fg="#666666"
            )

    def on_start(self):
        """
        Validate user inputs, warn on duplicate serials or missing cameras, and initiate capture.

        Temporarily hides the Tkinter window during the OpenCV session, then restores the window
        and re-probes cameras once the capture session terminates.
        """
        # 1. Read input values
        part_number = self.entry_part.get().strip()
        job_number = self.entry_job.get().strip()

        raw_sns = self.text_sn.get("1.0", "end").strip()
        serial_numbers = [line.strip() for line in raw_sns.splitlines() if line.strip()]

        # 2. Input validation
        if not part_number:
            messagebox.showerror("Missing Info", "Please enter a PART NUMBER.")
            self.entry_part.focus_set()
            return
        if not job_number:
            messagebox.showerror("Missing Info", "Please enter a JOB NUMBER.")
            self.entry_job.focus_set()
            return

        # Check for duplicate serial numbers
        seen_sns = set()
        duplicate_sns = []
        for sn in serial_numbers:
            if sn in seen_sns and sn not in duplicate_sns:
                duplicate_sns.append(sn)
            seen_sns.add(sn)
        if duplicate_sns:
            messagebox.showerror(
                "Duplicate Serial Number(s)",
                "The following serial number(s) were entered more than once:\n\n"
                + "\n".join(duplicate_sns)
                + "\n\nPlease remove the duplicate(s) and try again.",
            )
            return

        # Check camera warning
        if not self.detected_cameras:
            proceed = messagebox.askyesno(
                "No Camera Detected",
                "No cameras were detected during pre-check.\n\n"
                "Do you want to attempt starting anyway?",
                icon="warning"
            )
            if not proceed:
                return

        # 3. Hide the GUI while OpenCV runs, and restore GUI when capture window closes
        self.root.withdraw()
        try:
            capture.start_capture(
                part_number=part_number,
                job_number=job_number,
                serial_numbers=serial_numbers,
            )
        except Exception as e:
            messagebox.showerror("Capture Error", str(e))
        finally:
            self.root.destroy()
            self.check_cameras()


if __name__ == "__main__":
    CaptureGUI()

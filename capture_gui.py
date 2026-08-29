import os
import json
import tkinter as tk
from tkinter import messagebox, font
import threading
import capture

CONFIG_FILE = "camera_config.json"

class CaptureGUI:
    def __init__(self):
        # Window set up
        self.root = tk.Tk()
        self.root.title("Capture Dashboard")
        self.root.geometry("560x680")
        
        # State
        self.detected_cameras = []
        self.is_detecting_cameras = False
        self.cam_name_entries = {}

        # Create custom font objects
        text_font = font.Font(family="Segoe UI", size=14)
        bold_font = font.Font(family="Segoe UI", size=14, weight="bold")
        small_font = font.Font(family="Segoe UI", size=10)
        status_font = font.Font(family="Segoe UI", size=13, weight="bold")
        cam_details_font = font.Font(family="Segoe UI", size=11)
        btn_font = font.Font(family="Segoe UI", size=11)
        
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
            font=btn_font,
            command=self.refresh_cameras,
            padx=8,
            pady=2,
        )
        self.btn_refresh.pack(side="right")

        # Container for camera list with editable labels
        self.frame_cam_list = tk.Frame(self.frame_camera)
        self.frame_cam_list.pack(fill="x", pady=(4, 0))

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
        # Tag style for highlighting duplicate serial numbers
        self.text_sn.tag_configure("duplicate", background="#FFCDD2", foreground="#B71C1C")
        # Update the counter and check duplicates each time the operator types
        self.text_sn.bind("<KeyRelease>", self.update_sn_counter)

        # Live count of how many serial numbers are currently entered
        self.label_sn_count = tk.Label(self.root, text="0 serial number(s) entered",
                                       font=small_font, fg="#444444")
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

    # ---- Camera Config Storage ----
    def _load_cam_config(self):
        """Load saved camera names from JSON."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_cam_config(self, names_dict):
        """Save camera names to JSON."""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(names_dict, f, indent=2)
        except Exception:
            pass

    def refresh_cameras(self):
        """Starts asynchronous camera detection in a background thread."""
        if self.is_detecting_cameras:
            return
        
        self.is_detecting_cameras = True
        self.btn_refresh.config(state="disabled")
        self.label_cam_status.config(
            text="● Scanning camera devices... (please wait)",
            fg="#0055A5",
        )
        for child in self.frame_cam_list.winfo_children():
            child.destroy()

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
        self.cam_name_entries = {}

        for child in self.frame_cam_list.winfo_children():
            child.destroy()

        count = len(cameras)
        saved_names = self._load_cam_config()

        if count > 0:
            self.label_cam_status.config(
                text=f"● {count} camera(s) ready",
                fg="#2E7D32",  # Green
            )

            default_presets = ["Top View", "Side View", "Angle View", "Macro View"]

            for idx, cam in enumerate(cameras):
                cam_id = cam['id']
                default_name = saved_names.get(
                    str(cam_id), 
                    default_presets[idx] if idx < len(default_presets) else f"Camera {cam_id}"
                )

                row = tk.Frame(self.frame_cam_list)
                row.pack(fill="x", pady=2)

                tk.Label(
                    row,
                    text=f"  ● Camera {cam_id} ({cam['width']}x{cam['height']})",
                    font=font.Font(family="Segoe UI", size=10, weight="bold"),
                    fg="#2E7D32"
                ).pack(side="left")

                tk.Label(
                    row,
                    text="   Label: ",
                    font=font.Font(family="Segoe UI", size=9),
                    fg="#555555"
                ).pack(side="left")

                entry = tk.Entry(row, font=font.Font(family="Segoe UI", size=9), width=16)
                entry.insert(0, default_name)
                entry.pack(side="left")
                self.cam_name_entries[cam_id] = entry
        else:
            self.label_cam_status.config(
                text="● No cameras detected",
                fg="#C62828",  # Red
            )
            tk.Label(
                self.frame_cam_list,
                text="  Please connect your camera(s) and click 'Refresh'.",
                font=font.Font(family="Segoe UI", size=10),
                fg="#C62828"
            ).pack(anchor="w", pady=(2, 0))

    def update_sn_counter(self, event=None):
        # Remove previous duplicate highlights
        self.text_sn.tag_remove("duplicate", "1.0", "end")

        raw = self.text_sn.get("1.0", "end")
        lines = raw.splitlines()

        seen = {}  # sn -> list of line indices (1-indexed)
        count = 0
        for line_idx, line in enumerate(lines, start=1):
            cleaned = line.strip()
            if cleaned:
                count += 1
                seen.setdefault(cleaned, []).append(line_idx)

        duplicates = [sn for sn, line_nums in seen.items() if len(line_nums) > 1]

        if duplicates:
            # Highlight duplicate lines in red
            for sn in duplicates:
                for line_idx in seen[sn]:
                    self.text_sn.tag_add("duplicate", f"{line_idx}.0", f"{line_idx}.end")

            dup_preview = ", ".join(f"'{s}'" for s in duplicates)
            if len(dup_preview) > 35:
                dup_preview = dup_preview[:32] + "..."
            self.label_sn_count.config(
                text=f"{count} serial(s) entered  ⚠ Duplicate: {dup_preview}",
                fg="#C62828",
            )
        else:
            self.label_sn_count.config(
                text=f"{count} serial number(s) entered",
                fg="#444444",
            )

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

        # Flag duplicate serial numbers so the operator can fix them before capture starts
        counts = {}
        for sn in serial_numbers:
            counts[sn] = counts.get(sn, 0) + 1

        duplicate_sns = [sn for sn, c in counts.items() if c > 1]
        if duplicate_sns:
            dup_details = "\n".join(f"  • {sn} (entered {counts[sn]} times)" for sn in duplicate_sns)
            messagebox.showerror(
                "Duplicate Serial Number(s) Found",
                f"Duplicate serial number(s) were detected:\n\n"
                f"{dup_details}\n\n"
                f"Please remove or correct the duplicate serial number(s) before starting.",
            )
            return

        # 3. Read & Persist Camera Names
        camera_names = {}
        for cam in self.detected_cameras:
            cid = cam["id"]
            if cid in self.cam_name_entries:
                custom_name = self.cam_name_entries[cid].get().strip()
                camera_names[cid] = custom_name if custom_name else f"CAM{cid}"
            else:
                camera_names[cid] = f"CAM{cid}"

        self._save_cam_config({str(k): v for k, v in camera_names.items()})

        # 4. Hide the GUI while the OpenCV capture window runs on the main thread,
        #    then bring the GUI back once the session ends (ESC / window closed).
        self.root.withdraw()
        try:
            capture.start_capture(
                part_number=part_number,
                job_number=job_number,
                serial_numbers=serial_numbers,
                camera_names=camera_names,
            )
        except Exception as e:
            messagebox.showerror("Capture error", str(e))
        finally:
            self.root.destroy()


if __name__ == "__main__":
    CaptureGUI()

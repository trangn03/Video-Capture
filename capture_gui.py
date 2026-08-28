"""
capture_gui.py

A modern desktop dashboard built with CustomTkinter for configuring, validating,
and launching multi-camera capture sessions with OpenCV.

Features:
    - Sleek Dark / Light theme with modern card-based UI
    - Asynchronous camera diagnostics & status indicators
    - Part Number & Job Number metadata management
    - Output directory picker & quick "Open Folder" shortcut
    - Batch Serial Number queue with file import, duplicate detection, and live counter
    - Seamless handoff to high-speed OpenCV multi-camera capture window (capture.py)
    - Automatic dashboard restoration when capture session concludes
"""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import re

try:
    import customtkinter as ctk
except ImportError:
    # If customtkinter is not installed, provide helpful error guidance
    raise ImportError("CustomTkinter is required. Please install it using: pip install customtkinter")

import capture

# Configure global CustomTkinter appearance (matches OS System theme automatically)
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class CaptureGUI(ctk.CTk):
    """
    Modern desktop GUI for multi-camera capture session management.
    """

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Multi-Camera Capture Studio")
        self.geometry("640x780")
        self.minsize(580, 700)

        # State Variables
        self.detected_cameras = []
        self.is_checking_cameras = False
        self.output_dir = os.path.abspath(os.getcwd())

        # Build UI Components
        self._build_header()
        self._build_main_scrollable_container()
        self._build_camera_card()
        self._build_job_metadata_card()
        self._build_serial_queue_card()
        self._build_action_footer()

        # Keyboard shortcuts
        self.bind("<Control-Return>", lambda e: self.on_start())
        self.bind("<Command-Return>", lambda e: self.on_start())

        # Start initial camera probe in background
        self.check_cameras()

    # -------------------------------------------------------------------------
    # UI Layout Builders
    # -------------------------------------------------------------------------

    def _build_header(self):
        """Build top navigation header with branding."""
        header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(16, 6))

        title_label = ctk.CTkLabel(
            header_frame,
            text="📷 Capture Studio",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(anchor="w")

    def _build_main_scrollable_container(self):
        """Main scrollable area to hold dashboard cards."""
        self.scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=12)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def _build_camera_card(self):
        """Card 1: Hardware camera diagnostics & connectivity."""
        card = ctk.CTkFrame(self.scroll_frame, corner_radius=10)
        card.pack(fill="x", pady=(0, 12), padx=4)

        # Top row: Card Title + Rescan Button
        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(12, 6))

        card_title = ctk.CTkLabel(
            top_row,
            text="Hardware Diagnostics",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        card_title.pack(side="left")

        self.btn_refresh_cams = ctk.CTkButton(
            top_row,
            text="🔄 Rescan",
            width=80,
            height=26,
            font=ctk.CTkFont(size=12),
            command=self.check_cameras
        )
        self.btn_refresh_cams.pack(side="right")

        # Status & Description Row
        status_row = ctk.CTkFrame(card, fg_color="transparent")
        status_row.pack(fill="x", padx=16, pady=(0, 12))

        self.label_cam_status = ctk.CTkLabel(
            status_row,
            text="⏳ Checking for cameras...",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F59E0B"
        )
        self.label_cam_status.pack(anchor="w")

        self.label_cam_details = ctk.CTkLabel(
            status_row,
            text="Scanning for available cameras. Please wait...",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65"),
            anchor="w",
            justify="left"
        )
        self.label_cam_details.pack(anchor="w", pady=(2, 0))

    def _build_job_metadata_card(self):
        """Card 2: Part Number, Job Number, and Destination Folder."""
        card = ctk.CTkFrame(self.scroll_frame, corner_radius=10)
        card.pack(fill="x", pady=(0, 12), padx=4)

        header = ctk.CTkLabel(
            card,
            text="Job Information & Storage",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header.pack(anchor="w", padx=16, pady=(12, 10))

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=16, pady=(0, 14))

        # Part Number & Job Number in 2 columns
        grid_row = ctk.CTkFrame(content, fg_color="transparent")
        grid_row.pack(fill="x", pady=(0, 10))

        # Col 1: Part Number
        col1 = ctk.CTkFrame(grid_row, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 8))

        lbl_part = ctk.CTkLabel(col1, text="PART NUMBER *", font=ctk.CTkFont(size=11, weight="bold"))
        lbl_part.pack(anchor="w", pady=(0, 3))

        self.entry_part = ctk.CTkEntry(
            col1,
            placeholder_text="e.g. PN-98402",
            height=36,
            font=ctk.CTkFont(size=13)
        )
        self.entry_part.pack(fill="x")

        # Col 2: Job Number
        col2 = ctk.CTkFrame(grid_row, fg_color="transparent")
        col2.pack(side="right", fill="x", expand=True, padx=(8, 0))

        lbl_job = ctk.CTkLabel(col2, text="JOB NUMBER *", font=ctk.CTkFont(size=11, weight="bold"))
        lbl_job.pack(anchor="w", pady=(0, 3))

        self.entry_job = ctk.CTkEntry(
            col2,
            placeholder_text="e.g. 2026-001",
            height=36,
            font=ctk.CTkFont(size=13)
        )
        self.entry_job.pack(fill="x")

        # Save Directory Row
        lbl_dest = ctk.CTkLabel(content, text="SAVE DIRECTORY", font=ctk.CTkFont(size=11, weight="bold"))
        lbl_dest.pack(anchor="w", pady=(6, 3))

        dir_row = ctk.CTkFrame(content, fg_color="transparent")
        dir_row.pack(fill="x")

        self.entry_dest = ctk.CTkEntry(
            dir_row,
            height=34,
            font=ctk.CTkFont(size=12)
        )
        self.entry_dest.insert(0, self.output_dir)
        self.entry_dest.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_browse = ctk.CTkButton(
            dir_row,
            text="📁 Browse...",
            width=90,
            height=34,
            command=self._choose_directory
        )
        btn_browse.pack(side="left", padx=(0, 6))

        btn_open_folder = ctk.CTkButton(
            dir_row,
            text="📂 Open",
            width=70,
            height=34,
            fg_color="gray35",
            hover_color="gray25",
            command=self._open_current_directory
        )
        btn_open_folder.pack(side="right")

    def _build_serial_queue_card(self):
        """Card 3: Multiline Serial Numbers with helper tools."""
        card = ctk.CTkFrame(self.scroll_frame, corner_radius=10)
        card.pack(fill="x", pady=(0, 12), padx=4)

        # Header with Tools
        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(12, 6))

        title = ctk.CTkLabel(
            top_row,
            text="Serial Number Queue (Optional)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(side="left")

        # Action tools on top right of card
        tools_row = ctk.CTkFrame(top_row, fg_color="transparent")
        tools_row.pack(side="right")

        btn_paste = ctk.CTkButton(
            tools_row,
            text="📋 Paste",
            width=65,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="gray30",
            hover_color="gray20",
            command=self._paste_clipboard
        )
        btn_paste.pack(side="left", padx=(0, 4))

        btn_import = ctk.CTkButton(
            tools_row,
            text="📂 Import",
            width=68,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="gray30",
            hover_color="gray20",
            command=self._import_serials_file
        )
        btn_import.pack(side="left", padx=(0, 4))

        btn_clear = ctk.CTkButton(
            tools_row,
            text="🧹 Clear",
            width=60,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="gray30",
            hover_color="#991B1B",
            command=self._clear_serials
        )
        btn_clear.pack(side="right")

        # Multiline Serial Number Textbox
        self.text_sn = ctk.CTkTextbox(
            card,
            height=110,
            font=ctk.CTkFont(family="Courier", size=13),
            corner_radius=6
        )
        self.text_sn.pack(fill="x", padx=16, pady=(4, 6))
        self.text_sn.bind("<KeyRelease>", self.update_sn_counter)

        # Counter & Helper Banner
        bottom_row = ctk.CTkFrame(card, fg_color="transparent")
        bottom_row.pack(fill="x", padx=16, pady=(0, 12))

        self.label_sn_count = ctk.CTkLabel(
            bottom_row,
            text="📦 Auto SET Mode: captures will automatically increment by SET_#",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65"),
            anchor="w"
        )
        self.label_sn_count.pack(side="left", fill="x", expand=True)

        self.label_dup_warn = ctk.CTkLabel(
            bottom_row,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#EF4444",
            anchor="e"
        )
        self.label_dup_warn.pack(side="right")

    def _build_action_footer(self):
        """Bottom fixed action bar with Start button and quick guidance."""
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=24, pady=(4, 16))

        # Main Start Button
        self.btn_start = ctk.CTkButton(
            footer_frame,
            text="▶  START CAPTURE SESSION",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=46,
            corner_radius=8,
            fg_color="#10B981",
            hover_color="#059669",
            command=self.on_start
        )
        self.btn_start.pack(fill="x", pady=(0, 6))

        # Helpful Shortcuts Footer
        footer_tips = ctk.CTkLabel(
            footer_frame,
            text="In camera window:  [SPACE] Take Snapshot   •   [ESC] Exit & Return to Dashboard",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray60")
        )
        footer_tips.pack()

    # -------------------------------------------------------------------------
    # Camera Diagnostics Logic
    # -------------------------------------------------------------------------

    def check_cameras(self):
        """Asynchronously probe connected cameras without locking the GUI thread."""
        if self.is_checking_cameras:
            return

        self.is_checking_cameras = True
        self.btn_refresh_cams.configure(state="disabled", text="⏳ Checking...")
        self.label_cam_status.configure(
            text="⏳ Checking for cameras...",
            text_color="#F59E0B"
        )
        self.label_cam_details.configure(
            text="Scanning for available cameras. Please wait...",
            text_color=("gray40", "gray65")
        )

        def worker():
            cams = capture.detect_cameras(max_index=10)
            self.after(0, self._apply_camera_results, cams)

        threading.Thread(target=worker, daemon=True).start()

    def _apply_camera_results(self, cams):
        """Update UI elements with discovered camera information."""
        self.detected_cameras = cams
        self.is_checking_cameras = False
        self.btn_refresh_cams.configure(state="normal", text="🔄 Rescan")

        if cams:
            count = len(cams)
            cam_str = f"🟢 {count} Camera{'s' if count > 1 else ''} Ready"
            self.label_cam_status.configure(text=cam_str, text_color="#10B981")

            details_list = [f"Cam {c['id']}: {c['width']}x{c['height']}" for c in cams]
            self.label_cam_details.configure(
                text="Connected: " + "  |  ".join(details_list),
                text_color=("gray30", "gray80")
            )
        else:
            self.label_cam_status.configure(
                text="🔴 No Cameras Detected",
                text_color="#EF4444"
            )
            self.label_cam_details.configure(
                text="No video device found. Please verify USB connection and click Rescan.",
                text_color="#EF4444"
            )

    # -------------------------------------------------------------------------
    # Storage & Serial Helpers
    # -------------------------------------------------------------------------

    def _choose_directory(self):
        """Open directory picker modal."""
        chosen = filedialog.askdirectory(initialdir=self.output_dir, title="Select Output Folder")
        if chosen:
            self.output_dir = chosen
            self.entry_dest.delete(0, "end")
            self.entry_dest.insert(0, self.output_dir)

    def _open_current_directory(self):
        """Open destination directory in OS file manager (Explorer/Finder/xdg-open)."""
        target = self.entry_dest.get().strip() or self.output_dir
        if not os.path.exists(target):
            os.makedirs(target, exist_ok=True)

        try:
            if sys.platform == "darwin":
                subprocess.run(["open", target], check=False)
            elif os.name == "nt":
                os.startfile(target)
            else:
                subprocess.run(["xdg-open", target], check=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")

    def _paste_clipboard(self):
        """Paste clipboard content into the serial number textbox."""
        try:
            clipboard = self.clipboard_get()
            self.text_sn.insert("end", clipboard + "\n")
            self.update_sn_counter()
        except Exception:
            pass

    def _import_serials_file(self):
        """Import serial numbers from a plain text or CSV file."""
        file_path = filedialog.askopenfilename(
            title="Import Serial Numbers",
            filetypes=[("Text & CSV Files", "*.txt *.csv"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.strip() for line in f if line.strip()]
            if lines:
                self.text_sn.insert("end", "\n".join(lines) + "\n")
                self.update_sn_counter()
        except Exception as e:
            messagebox.showerror("Import Error", f"Could not read file:\n{e}")

    def _clear_serials(self):
        """Clear the serial numbers input box."""
        self.text_sn.delete("1.0", "end")
        self.update_sn_counter()

    def update_sn_counter(self, event=None):
        """Update live serial numbers counter and check for duplicate entries."""
        raw = self.text_sn.get("1.0", "end").strip()
        items = [p.strip() for p in re.split(r'[,\s]+', raw) if p.strip()]
        count = len(items)

        # Duplicate check
        seen = set()
        duplicates = set()
        for sn in items:
            if sn in seen:
                duplicates.add(sn)
            seen.add(sn)

        if duplicates:
            self.label_dup_warn.configure(text=f"⚠️ {len(duplicates)} Duplicate(s)")
        else:
            self.label_dup_warn.configure(text="")

        if count > 0:
            self.label_sn_count.configure(
                text=f"⚡ {count} serial number(s) queued for capture",
                text_color="#10B981"
            )
        else:
            self.label_sn_count.configure(
                text="📦 Auto SET Mode: captures will automatically increment by SET_#",
                text_color=("gray40", "gray65")
            )

    # -------------------------------------------------------------------------
    # Start Capture Action
    # -------------------------------------------------------------------------

    def on_start(self):
        """Validate input values, hide dashboard, run OpenCV capture, and restore."""
        part_number = self.entry_part.get().strip()
        job_number = self.entry_job.get().strip()
        dest_dir = self.entry_dest.get().strip() or self.output_dir

        raw_sns = self.text_sn.get("1.0", "end").strip()
        serial_numbers = [p.strip() for p in re.split(r'[,\s]+', raw_sns) if p.strip()]

        # Validation
        if not part_number:
            messagebox.showerror("Missing Information", "Please enter a PART NUMBER before starting.")
            self.entry_part.focus_set()
            return

        if not job_number:
            messagebox.showerror("Missing Information", "Please enter a JOB NUMBER before starting.")
            self.entry_job.focus_set()
            return

        # Check for duplicates
        seen = set()
        duplicates = []
        for sn in serial_numbers:
            if sn in seen and sn not in duplicates:
                duplicates.append(sn)
            seen.add(sn)

        if duplicates:
            messagebox.showerror(
                "Duplicate Serial Numbers",
                "The following serial numbers appear multiple times:\n\n"
                + "\n".join(duplicates[:10])
                + ("\n..." if len(duplicates) > 10 else "")
                + "\n\nPlease correct or remove duplicates before starting."
            )
            return

        # Warning if no cameras detected
        if not self.detected_cameras:
            proceed = messagebox.askyesno(
                "No Camera Detected",
                "No cameras were found during the diagnostics check.\n\n"
                "Do you want to attempt starting the capture session anyway?",
                icon="warning"
            )
            if not proceed:
                return

        # Hide dashboard during live OpenCV window session
        self.withdraw()

        def capture_thread():
            try:
                capture.start_capture(
                    part_number=part_number,
                    job_number=job_number,
                    serial_numbers=serial_numbers,
                    output_dir=dest_dir
                )
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Capture Error", str(e)))
            finally:
                # Restore dashboard and refresh camera status
                self.after(0, self._restore_dashboard)

        threading.Thread(target=capture_thread, daemon=True).start()

    def _restore_dashboard(self):
        """Restore window visibility and re-verify camera health."""
        self.deiconify()
        self.check_cameras()


if __name__ == "__main__":
    app = CaptureGUI()
    app.mainloop()

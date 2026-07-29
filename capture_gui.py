import tkinter as tk
from tkinter import messagebox, font
import capture

class CaptureGUI:
    def __init__(self):
        # Window set up
        self.root = tk.Tk()
        self.root.title("Capture Dashboard")
        self.root.geometry("550x550")
        
        # Create a custom font object
        text_font = font.Font(family="Segoe UI", size= 18)
        
        # Entering part number
        self.label_part = tk.Label(self.root, text = "Enter PART NUMBER:", font=text_font)
        self.label_part.pack(padx=10, pady=10)
        
        self.entry_part = tk.Entry(self.root, font=text_font, justify="center")
        self.entry_part.pack(padx=10, pady=10)
        
        # Entering job number 
        self.label_job = tk.Label(self.root, text = "Enter JOB NUMBER:", font=text_font)
        self.label_job.pack(padx=10, pady=10)
        
        self.entry_job = tk.Entry(self.root, font=text_font, justify="center")
        self.entry_job.pack(padx=10, pady=10)
        
        # Entering serial number
        self.label_sn = tk.Label(self.root, text="Enter SERIAL NUMEBRS one per line: ", font=text_font)
        self.label_sn.pack(padx=10, pady=10)
        
        self.text_sn = tk.Text(self.root, height = 5, width=30, font=text_font)
        self.text_sn.pack(padx=10, pady=(10, 0))
        # Update the counter each time the operator types in the serial box
        self.text_sn.bind("<KeyRelease>", self.update_sn_counter)

        # Live count of how many serial numbers are currently entered
        self.label_sn_count = tk.Label(self.root, text="0 serial number(s) entered",
                                       font=font.Font(family="Segoe UI", size=11))
        self.label_sn_count.pack(padx=10, pady=(2, 10))

        # Start the capture button
        self.btn_start = tk.Button (
            self.root,
            text="Start Capture",
            font=text_font,
            bg="#4CAF50",
            fg="black",
            command=self.on_start,   # run on_start() when clicked
        )
        self.btn_start.pack(padx=10, pady=10)

        self.root.mainloop()

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


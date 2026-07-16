import tkinter as tk
from tkinter import messagebox
import capture

class CaptureGUI:
    def __init__(self):
        # Window set up
        self.root = tk.Tk()
        self.root.title("Capture Dashboard")
        self.root.geometry("500x500")
        
        # Entering part number
        self.label_part = tk.Label(self.root, text = "Enter PART NUMBER:", font=('Arial', 18))
        self.label_part.pack(padx=10, pady=10)
        
        self.entry_part = tk.Entry(self.root, font=('Arial', 18), justify="center")
        self.entry_part.pack(padx=10, pady=10)
        
        # Entering job number 
        self.label_job = tk.Label(self.root, text = "Enter JOB NUMBER:", font=('Arial', 18))
        self.label_job.pack(padx=10, pady=10)
        
        self.entry_job = tk.Entry(self.root, font=('Arial', 18), justify="center")
        self.entry_job.pack(padx=10, pady=10)
        
        # Entering serial number
        self.label_sn = tk.Label(self.root, text="Enter SERIAL NUMEBRS one per line: ", font=('Arial', 18))
        self.label_sn.pack(padx=10, pady=10)
        
        self.text_sn = tk.Text(self.root, height = 5, width=30, font=('Arial', 18))
        self.text_sn.pack(padx=10, pady=10)
        
        # Start the capture button
        self.btn_start = tk.Button (
            self.root, 
            text="Start Capture",
            font=('Arial', 18),
            bg="#4CAF50",
            fg="black",
            command=self.launch_cameras
        )
        self.btn_start.pack(padx=10, pady=10)
        
        self.root.mainloop()
        
    def launch_cameras(self):
        part_number = self.entry_part.get().strip()
        job_number = self.entry_job.get().strip()
            
        raw_sn_text = self.text_sn.get("1.0", tk.END).strip()
            
        if not part_number or not job_number:
            messagebox.showwarning(title="Missing Info", message=f"Please enter both part number and job number")
            return
            
        # Convert the raw text box block into a list
        serial_numbers_list = []
        raw_lines = raw_sn_text.split('\n')
        for sn in raw_lines:
            clean_sn = sn.strip()
            if clean_sn != "":
                serial_numbers_list.append(clean_sn)
            
        self.root.withdraw()
            
        # Start the connection with capture.py
        try:
            capture.start_capture(part_number, job_number, serial_numbers_list)
        except Exception as e:
            print(f"Error during capture: {e}")
            messagebox.showerror(title="Crash", message=f"The camera session crashed:\n{e}")
        # Check if the user enter everything
        self.root.destroy()

if __name__ == "__main__":
    CaptureGUI()


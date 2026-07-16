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
        )
        self.btn_start.pack(padx=10, pady=10)
        
        self.root.mainloop()
        

if __name__ == "__main__":
    CaptureGUI()


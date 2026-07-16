import tkinter as tk
import tkinter as messagebox
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
        
        

        self.root.mainloop()

if __name__ == "__main__":
    CaptureGUI()


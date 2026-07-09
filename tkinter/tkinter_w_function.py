import tkinter as tk

class myGUI:
    def __init__(self):
        self.root = tk.Tk()
        
        self.label = tk.Label(self.root, text ="Your message", font=('Arial', 18))
        self.label.pack(padx=10, pady=10)
        
        self.textbox = tk.Text(self.root, height=5, font=('Arial',18))
        self.textbox.pack(padx=10, pady=10) 
        
        self.check_state = tk.IntVar() 
        
        self.check = tk.Checkbutton(self.root, text="Show Message", font=('Arial', 18), variable=self.check_state)
        self.check.pack(padx=10, pady=10)     
              
        self.button = tk.Button(self.root, text="Show message", font=('Arial', 18), command=self.show_message)
        self.button.pack(padx=10, pady=10)
              
        self.root.mainloop()
        
    def show_message(self): 
        print(self.check_state.get())
        
myGUI()
        

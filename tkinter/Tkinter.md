# Tkinter

## Basic Form
1. Import
   ```
   import tkinter as tk
   ```
1. Initialization & Main Loop
   ```
   self.root = tk.Tk()
   # ... widget set up 
   self.root.mainloop()
   ```
2. Create window 
   ```
   root.geometry("500x500)
   ```
3. Add title
    ```
    root.title("My first GUI")
    ```

## Inside the window -> Widget
1. Create object
   ```
   label = tk.Label(root, text="Hello World!", font =('Arial', 18))
   label.pack(padx=20, pady=20)
   ```
2. Input the text
   ```
   textbox = tk.Text(root, height=3, font=('Arial', 16))
   textbox.pack(padx=10)
   ```
3. Entry
   ```
   myentry = tk.Entry(root)
   myentry.pack()
   ```
4. Button
   ```
   button = tk.Button(root, text="Click me", font=('Arial',18))
   button.pack(padx=10, pady=10)
   ```
5. CheckButton
   ```
   self.check_state = tk.IntVar() 
   self.check = tk.Checkbutton(self.root, text="Show Message", variable=self.check_state)

   ```
6. Menu
   ```
   self.menu = tk.Menu(self.root)
   
   self.filemenu = tk.Menu(self.menu, tearoff=0)
   self.filemenu.add_command(label="Close", command=exit)
   
   self.menu.add_cascade(menu=self.filemenu, label="File")
   self.root.config(menu=self.menu)
   ```
7. Event Binding
   ```
   
   ```
8. 

   
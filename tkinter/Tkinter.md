# Tkinter

## Basic Form
1. Import
   ```python
   import tkinter as tk
   ```
1. Initialization & Main Loop
   ```python
   self.root = tk.Tk()
   # ... widget set up 
   self.root.mainloop()
   ```
2. Create window 
   ```python
   root.geometry("500x500)
   ```
3. Add title
    ```python
    root.title("My first GUI")
    ```

## Inside the window -> Widget
1. Create object
   ```python
   label = tk.Label(root, text="Hello World!", font =('Arial', 18))
   label.pack(padx=20, pady=20)
   ```
2. Input the text
   ```python
   textbox = tk.Text(root, height=3, font=('Arial', 16))
   textbox.pack(padx=10)
   ```
3. Entry
   ```python
   myentry = tk.Entry(root)
   myentry.pack()
   ```
4. Button
   ```python
   button = tk.Button(root, text="Click me", font=('Arial',18))
   button.pack(padx=10, pady=10)
   ```
5. CheckButton
   ```python
   self.check_state = tk.IntVar() 
   self.check = tk.Checkbutton(self.root, text="Show Message", variable=self.check_state)
   ```
6. Menu
   ```python
   self.menu = tk.Menu(self.root)
   
   # Create a file menu dropdown
   self.filemenu = tk.Menu(self.menu, tearoff=0)
   self.filemenu.add_command(label="Close", command=exit)
   
   # Create an action menu dropdown
   self.actionmenu = tk.Menu(self.menu, tearoff=0)
   self.actionmenu.add_command(label="Show Message", command=self.show_message)

   # Attach dropdowns to the main menu 
   self.menu.add_cascade(menu=self filemenu, label="File")
   self.menu.add_cascade(menu=self.actionmenu, label="Action")
   self.root.config(menu=self.menu)
   ```
7. Event Binding
   ```python
   # Bind the Text box so that pressing any key triggers self.shortcut
   self.textbox.bind("<KeyPress>", self.shortcut)

   def shortcut(self, event):
      # event.state == 12 is 'Ctrl', event.keysym == "Return" is the 'Enter' key
      if event.state == 12 and event.keysym == "Return":
         self.show_message()
   ```
8. Window Protocols
   ```python
   # Trigger 'self.on_closing' when the user clicks the window's 'X' button
   self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

   def on_closing(self):
      # Ask for confirmation before destroying the window
      if messagebox.askokcancel("Quit", "Do you want to quit?"):
         self.root.destroy()
   ```
9.  Message Boxes
   ```python
   def show_message(self):
      # Get text from line 1, character 0 ('1.0') to the END of the textbox
    message_content = self.textbox.get('1.0', tk.END)

      if self.check_state.get() == 0:
         print(message_content)
      else:
         messagebox.showinfo(title="Message" message=message_content)

   ```
10. Deleting Text
   ```python
   def clear(self):
      # Delete all content in the textbox
      self.textbox.delete('1.0', tk.END)
   ```
   
# Tkinter

## Basic Form
1. Create window 
   ```
   root.geometry("500x500)
   ```
2. Add title
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
   
   ```
6. 

   
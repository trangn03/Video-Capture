import tkinter as tk
root = tk.Tk()

# Create window with 800x500
root.geometry("500x500")

# Add title for the window
root.title("My first gui")

# Inside the window, widget
# Create object and use layout to get the object
label = tk.Label(root, text="Hello World!", font =('Arial', 18))
label.pack(padx=20, pady=20)

# Input the text
textbox = tk.Text(root, height=3, font=('Arial', 16))
textbox.pack(padx=10)

# Entry
myentry = tk.Entry(root)
myentry.pack()

# Button
button = tk.Button(root, text="Click me", font=('Arial',18))
button.pack(padx=10, pady=10)

# Grid layout
buttonframe = tk.Frame(root)
buttonframe.columnconfigure(0, weight=1)
buttonframe.columnconfigure(1, weight=1)
buttonframe.columnconfigure(2, weight=1)
btn1 = tk.Button(buttonframe, text="1", font=('Arial', 18))
btn1.grid(row=0, column=0, sticky=tk.W + tk.E)

btn2 = tk.Button(buttonframe, text="2", font=('Arial', 18))
btn2.grid(row=0, column=1, sticky=tk.W + tk.E)

btn3 = tk.Button(buttonframe, text="3", font=('Arial', 18))
btn3.grid(row=0, column=2, sticky=tk.W + tk.E)

btn4 = tk.Button(buttonframe, text="4", font=('Arial', 18))
btn4.grid(row=1, column=0, sticky=tk.W + tk.E)

btn5 = tk.Button(buttonframe, text="5", font=('Arial', 18))
btn5.grid(row=1, column=1, sticky=tk.W + tk.E)

btn6 = tk.Button(buttonframe, text="6", font=('Arial', 18))
btn6.grid(row=1, column=2, sticky=tk.W + tk.E)
# sticky

# fill x is fit all them in horizontal direction
buttonframe.pack(fill='x')

# another button 
anotherbtn = tk.Button(root, text ="TEST")
anotherbtn.place(x=200, y=200, height=100, width=100)
anotherbtn.pack()

root.mainloop()



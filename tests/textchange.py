import tkinter as tk
import time

def update_label():
    # This automatically updates the label on the screen
    text_var.set("Text updated via StringVar!")
    
def label_loop():
	for n in range(10):
		text_var.set(f"n = {n}")
		root.update()
		time.sleep(1.0)

root = tk.Tk()
root.geometry("300x150")

# 1. Initialize the StringVar
text_var = tk.StringVar()
text_var.set("This is the starting text.")

# 2. Link it to a Label using 'textvariable'
label = tk.Label(root, textvariable=text_var, font=("Arial", 12))
label.pack(pady=20)

# 3. Create a button to trigger the change
btn = tk.Button(root, text="Click to Change", command=update_label)
btn.pack()

btn2 = tk.Button(root, text="Loop Text", command=label_loop)
btn2.pack()


root.mainloop()

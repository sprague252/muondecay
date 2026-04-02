import time, random

import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from collections import deque
import queue
import threading

def data_producer(q):
    while True:
        q.put(random.randint(0, 9))
        time.sleep(0.1)

class HistogramApp:
    def __init__(self, root, q):
        self.root = root
        self.q = q
        self.paused = False
        self.data = deque(maxlen=1000)

        # Figure
        self.fig = Figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Live Histogram (hist())")
        #self.ax.set_ylim(0, 30)

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()

        # Controls
        controls = tk.Frame(root)
        controls.pack(pady=5)

        tk.Button(controls, text="Pause", command=self.pause).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="Resume", command=self.resume).pack(side=tk.LEFT, padx=5)

        self.update_histogram()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def update_histogram(self):
        if not self.paused:
            while not self.q.empty():
                self.data.append(self.q.get())

            self.ax.clear()
            self.ax.hist(self.data, bins=10, range=(0, 10), edgecolor="black")
            #self.ax.set_ylim(0, 30)
            self.ax.set_title("Live Histogram (hist())")

            self.canvas.draw_idle()

        self.root.after(100, self.update_histogram)

root = tk.Tk()
root.title("Histogram using hist()")

q = queue.Queue()
threading.Thread(target=data_producer, args=(q,), daemon=True).start()

HistogramApp(root, q)
root.mainloop()
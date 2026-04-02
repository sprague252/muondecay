import threading
import queue
import random
import time

import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from collections import deque
import queue

def data_producer(q):
    while True:
        q.put(random.randint(0, 9))
        time.sleep(0.1)

class HistogramApp:
    def __init__(self, root, q):
        self.root = root
        self.q = q

        self.data = deque(maxlen=100)

        fig = Figure(figsize=(5, 4))
        self.ax = fig.add_subplot(111)
        self.bar_container = self.ax.bar(range(10), [0] * 10)

        self.ax.set_ylim(0, 30)
        self.ax.set_title("Live Histogram")

        self.canvas = FigureCanvasTkAgg(fig, master=root)
        self.canvas.get_tk_widget().pack()

        self.update_histogram()

    def update_histogram(self):
        while not self.q.empty():
            self.data.append(self.q.get())

        counts = [0] * 10
        for v in self.data:
            counts[v] += 1

        for rect, count in zip(self.bar_container, counts):
            rect.set_height(count)

        self.canvas.draw_idle()
        self.root.after(100, self.update_histogram)

root = tk.Tk()
q = queue.Queue()

threading.Thread(target=data_producer, args=(q,), daemon=True).start()

app = HistogramApp(root, q)
root.mainloop()
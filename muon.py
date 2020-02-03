#! /usr/bin/env python
import argparse
import numpy as np
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import re
import scipy.interpolate as interp
import tkinter as tk
#import tk.messagebox
from os import system, getcwd, chdir
#import os.path as path
from platform import system as platform

class Param:

    def __init__(self, master, label, val, row=None, show=True):
        self.name = label
        self.label = tk.Label(master, text=label+':')
        vtext = '{:g}'.format(val)
        self.value = tk.Label(master, text=vtext)
        if show:
            if row == None:
                self.label.grid(column=0, sticky=tk.E)
                self.value.grid(column=1, columnspan=2, sticky=tk.E)
            else:
                self.label.grid(row=row, column=0, sticky=tk.E)
                self.value.grid(row=row, column=1, columnspan=2, sticky=tk.E)
    

class Param_Array:

    def __init__(self, master, label, val, row=None, show=True):
        self.label = tk.Label(master, text=label+':')
        self.entry = tk.Entry(master)
        self.entry.insert(0, ', '.join(map(str,val)))
        if show:
            if row == None:
                self.label.grid(column=0, sticky=tk.E)
                self.entry.grid(column=1, columnspan=2, sticky=tk.E)
            else:
                self.label.grid(row=row, column=0, sticky=tk.E)
                self.entry.grid(row=row, column=1, columnspan=2, sticky=tk.E)

master = tk.Tk()
master.title('Muon Data Collection')

left_frame = tk.Frame(master)
left_frame.grid(row=0, column=0,sticky=tk.NW)
right_frame = tk.Frame(master)
right_frame.grid(row=0, column=1,sticky=tk.NW)

control_frame = tk.LabelFrame(left_frame, text="Control", padx=75)
control_frame.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N)
config_button = tk.Button(control_frame,  text="Configure", width=10)
config_button.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
config_button.columnconfigure(0, weight=1)
config_button.rowconfigure(0, weight=1)
start_button = tk.Button(control_frame,  text="Start", width=10)
start_button.grid(row=1, column=0, sticky=tk.W+tk.E+tk.N)
pause_button = tk.Button(control_frame,  text="Pause", width=10)
pause_button.grid(row=2, column=0, sticky=tk.W+tk.E+tk.N)
fit_button = tk.Button(control_frame,  text="Fit", width=10)
fit_button.grid(row=3, column=0, sticky=tk.W+tk.E+tk.N)
rawdata_button = tk.Button(control_frame,  text="View Raw Data", width=10)
rawdata_button.grid(row=4, column=0, sticky=tk.W+tk.E+tk.N)
quit_button = tk.Button(control_frame,  text="Quit", width=10, 
    foreground="red")
quit_button.grid(row=5, column=0, sticky=tk.W+tk.E+tk.N)

monitor_frame = tk.LabelFrame(left_frame, text="Monitor", padx=75, pady=5)
monitor_frame.grid(row=1, column=0, sticky=tk.W+tk.E+tk.N)
tt=0
nmuon=0
muonrate=0
ndecays=0
decayrate=0
etime_Param = Param(monitor_frame, 'Elapsed Time', tt, row=0)
nmuon_Param = Param(monitor_frame, 'Number of Muons', nmuon, row=1)
muonrate_Param = Param(monitor_frame, 'Muon Rate (1/s)', muonrate, row=2)
ndecays_Param = Param(monitor_frame, 'Muon Decays', ndecays, row=3)
decayrate_Param = Param(monitor_frame, 'Decay Rate (1/min)', decayrate, row=4)

rate_frame  = tk.LabelFrame(left_frame, text="Rate Meter", padx=5, pady=5)
rate_frame.grid(row=2, column=0, sticky=tk.W+tk.E+tk.N)

ratefig = Figure(figsize=(3, 2), dpi=100)
t = np.arange(0, 3, .01)
ratefig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))
canvas = FigureCanvasTkAgg(ratefig, master=rate_frame)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.W+tk.E+tk.N)


histogram_frame = tk.LabelFrame(right_frame, text="Muon Decay Time Histogram", 
    padx=5, pady=5)
histogram_frame.grid(row=0, column=0, sticky=tk.NW)
linlog_button = tk.Button(histogram_frame,  text="Change y-scale Linear/Log", width=20)
linlog_button.grid(row=0, column=0, sticky=tk.W)
export_button = tk.Button(histogram_frame,  text="Export Histogram", width=20)
export_button.grid(row=0, column=1, sticky=tk.E)

fig = Figure(figsize=(5, 4), dpi=100)
t = np.arange(0, 3, .01)
fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))
canvas = FigureCanvasTkAgg(fig, master=histogram_frame)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().grid(row=1, column=0, columnspan=2, sticky=tk.W+tk.E+tk.N)

detector_frame = tk.LabelFrame(right_frame, text="Muons Through Detector", 
    width=400, height=100, padx=5, pady=5)
detector_frame.grid(row=1, column=0, sticky=tk.W+tk.E+tk.N)


# Switch window focus to the Python app on a Mac.
if platform() == 'Darwin':  # How Mac OS X is identified by Python
    system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "python" to true' ''')

master.mainloop()

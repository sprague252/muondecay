#! /usr/bin/env python

import argparse
import re
from multiprocessing import Process, Value, Array
import os      
import sys
import tkinter as tk
import tkinter.filedialog as filedialog
import numpy as np

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import scipy.interpolate as interp
from serial.tools.list_ports import comports

from detect import detectGUI


def muon_GUI():    

    class Param:

        def __init__(self, master, label, val, foreground="black",
            row=None, show=True):
            self.name = label
            self.label = tk.Label(master, text=label+':',
                foreground=foreground)
            vtext = '{:g}'.format(val)
            self.value = tk.Label(master, text=vtext,
                foreground=foreground)
            if show:
                if row == None:
                    self.label.grid(column=0, sticky=tk.E)
                    self.value.grid(column=1, columnspan=2, sticky=tk.E)
                else:
                    self.label.grid(row=row, column=0, sticky=tk.E)
                    self.value.grid(row=row, column=1, columnspan=2,
                        sticky=tk.E)
    

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
                    self.entry.grid(row=row, column=1, columnspan=2,
                        sticky=tk.E)
            
    def open_config_window(params):
        global config_win
        ports = comports()
        devs = []
        for port in ports:
            devs = devs + [port.device]
        try:
            if config_win.state() == 'normal':
                config_win.focus()
        except:
            config_win = tk.Toplevel()
            config_win.title("Output File Configuration")
            port_frame = tk.LabelFrame(config_win, text="Select " +
                "Port", foreground="black")
            port_frame.pack()
            for dv in devs:
                dv_rbutton = tk.Radiobutton(port_frame, text=dv, 
                    foreground="black", variable=params["device"], value=dv)
                dv_rbutton.pack(anchor=tk.W)
            outfile_frame = tk.LabelFrame(config_win, text="Output" +
                " File", foreground="black")
            outfile_frame.pack()
            outfile_button = tk.Button(outfile_frame, text="Select" +
                " File", foreground="black", command = lambda:
                outfile_dialog(params, config_win))
            outfile_button.grid(row=0, column=0)
            outfile_label = tk.Label(outfile_frame,
                textvariable=params["outfname"], foreground="black")
            outfile_label.grid(row=0, column=1)
            params["appnd"] = tk.BooleanVar()
            params["appnd"].set(False)
            appnd_check = tk.Checkbutton(outfile_frame, 
                text="Append to File", variable=params["appnd"],
                foreground="black")
            appnd_check.grid(row=1, column=1, sticky=tk.E)
            dt_frame = tk.LabelFrame(config_win, text="Detect " +
                "Time", foreground="black")
            dt_frame.pack()
            params["dtime"] = tk.IntVar()
            dttext = ['1 h', '1 d', '2 d', '7 d', 'Enter time (s):']
            dtvals = [3600, 24 * 3600, 2 * 24 * 3600, 7 * 24 * 3600, -999]
            dtentry = tk.Entry(dt_frame, width="10",
                foreground="black", background="white",
                textvariable=params["dtstr"])
#                text=params["dtstr"].get()) 
            def showtext():
                dtval = params["dtime"].get()
                if dtval == -999:
                    dtentry.configure(state="normal")
                else:
                    dtentry.configure(state="disable")
                    params['dtstr'].set(str(dtval))
            for dt in range(4):
                dt_rbutton = tk.Radiobutton(dt_frame,
                    text=dttext[dt], foreground="black",
                    variable=params["dtime"], value=dtvals[dt],
                    command=showtext)
                dt_rbutton.pack(anchor=tk.W)
            dt_rbutton = tk.Radiobutton(dt_frame, text=dttext[4],
                foreground="black", variable=params["dtime"],
                value=dtvals[4], command=showtext)
            dt_rbutton.pack(anchor=tk.W)
            dtentry.pack(anchor=tk.E)
            dtentry.configure(state='disabled')
            ok_button = tk.Button(config_win, text="OK",
                foreground="black", command=config_win.destroy)
            ok_button.pack()       


    def outfile_dialog(params):
        fname = params["outfname"].get()
        if os.path.dirname(fname):
            idir = os.path.dirname(fname)
        else:
            idir = os.curdir
#         fname = filedialog.asksaveasfilename(parent=config_win, 
#             initialdir=idir, initialfile=os.path.basename(fname))
        fname = filedialog.asksaveasfilename(initialdir=idir,
            initialfile=os.path.basename(fname))
        if fname:
            params["outfname"].set(fname)
    def open_plot_window():
        global plot_win
        global nbins
        global fitmethod
        try:
            if plot_win.state() == 'normal':
                plot_win.focus()
        except:
            plot_win = tk.Toplevel()
            plot_win.title("Plot Configuration")
            bins_frame = tk.LabelFrame(plot_win, text="Number " +
                "of Histogram Bins", foreground="black")
            bins_frame.pack()
            for nb in ["5", "10", "20"]:
                nb_rbutton = tk.Radiobutton(bins_frame, text=nb, 
                    foreground="black", variable=nbins_choice, value=nb)
                nb_rbutton.pack(anchor=tk.W)
            # Add an other value choice with value -1.
            nb_rbutton = tk.Radiobutton(bins_frame, text="Other Value", 
                    foreground="black", variable=nbins_choice, value="-1")
            nb_rbutton.pack(anchor=tk.W)
            fit_frame = tk.LabelFrame(plot_win, text="Fit " +
                "Method", foreground="black")
            fit_frame.pack()
            fit_rbutton = tk.Radiobutton(fit_frame, text="Nonlinear fit", 
                    foreground="black", variable=fitmethod, value="0")
            fit_rbutton.pack(anchor=tk.W)
            fit_rbutton = tk.Radiobutton(fit_frame, 
                text="Background subtract", foreground="black",
                variable=fitmethod, value="1")
            fit_rbutton.pack(anchor=tk.W)
            ok_button = tk.Button(plot_win, text="OK",
                foreground="black", command=plot_win.destroy)
            ok_button.pack()       

    
    def detect_run(params):
        from tkinter import messagebox
        vartxt = "port: {:}, outfile: {:}".format(
            params["device"].get(), params["outfname"].get())
        messagebox.showinfo("Variables", vartxt)
#         detectp = Process(target=detectGUI, args=(port, outfile,
#             appnd, sampletime, ndecays, killswitch))
#         detectp.start()
#         return detectp
 
        
        
    def quit_dialog():
        from tkinter import messagebox
        answer = messagebox.askyesno("Question","Do you want to quit?")
        if answer==True:
           master.destroy()     
  

    master = tk.Tk()
    master.title('Muon Data Collection')
    
    params = {}
    params["outfname"] = tk.StringVar()
    params["outfname"].set('muon_data.txt')
    params["device"] = tk.StringVar()
    params["device"].set("/dev/null")
    params["dtstr"] = tk.StringVar()
    params["dtstr"].set("")
    params["nbins_choice"] = tk.StringVar()
    params["nbins_choice"].set('20')
    params["fitmethod"] = tk.StringVar()
    params["fitmethod"].set('0')
    

    left_frame = tk.Frame(master)
    left_frame.grid(row=0, column=0,sticky=tk.NW)
    right_frame = tk.Frame(master)
    right_frame.grid(row=0, column=1,sticky=tk.NW)



    control_frame = tk.LabelFrame(left_frame, text="Control",
        foreground="black", padx=75)
    control_frame.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N)
    config_button = tk.Button(control_frame,  text="Configure Detection",
        width=10, foreground="black")
    config_button['command'] = lambda: open_config_window(params)
    config_button.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
    config_button.columnconfigure(0, weight=1)
    config_button.rowconfigure(0, weight=1)

    plot_config_button = tk.Button(control_frame,  text="Configure Plot",
        width=10, foreground="black")
    plot_config_button['command'] = open_plot_window
    plot_config_button.grid(row=1, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
    plot_config_button.columnconfigure(0, weight=1)
    plot_config_button.rowconfigure(1, weight=1)


    start_button = tk.Button(control_frame, text="Start Detection", width=10,
        foreground="black")
    start_button['command'] = lambda : detect_run(params)
    start_button.grid(row=2, column=0, sticky=tk.W+tk.E+tk.N)
    pause_button = tk.Button(control_frame, text="Pause Detection", width=10,
        foreground="black")
    pause_button.grid(row=3, column=0, sticky=tk.W+tk.E+tk.N)
    fit_button = tk.Button(control_frame, text="Fit", width=10,
        foreground="black")
    fit_button.grid(row=4, column=0, sticky=tk.W+tk.E+tk.N)
    rawdata_button = tk.Button(control_frame, text="View Raw Data",
        width=10, foreground="black")
    rawdata_button.grid(row=5, column=0, sticky=tk.W+tk.E+tk.N)
    quit_button = tk.Button(control_frame, text="Quit", width=10, 
        foreground="red")
    quit_button['command'] = quit_dialog
    quit_button.grid(row=6, column=0, sticky=tk.W+tk.E+tk.N)

    monitor_frame = tk.LabelFrame(left_frame, text="Monitor",
        foreground="black", padx=75, pady=5)
    monitor_frame.grid(row=1, column=0, sticky=tk.W+tk.E+tk.N)
    tt=0
    nmuon=0
    muonrate=0
    ndecays=0
    decayrate=0
    etime_Param = Param(monitor_frame, 'Elapsed Time', tt, row=0)
    nmuon_Param = Param(monitor_frame, 'Number of Muons', nmuon, row=1)
    muonrate_Param = Param(monitor_frame, 'Muon Rate (1/s)', muonrate,
        row=2)
    ndecays_Param = Param(monitor_frame, 'Muon Decays', ndecays, row=3)
    decayrate_Param = Param(monitor_frame, 'Decay Rate (1/min)',
        decayrate, row=4)

    rate_frame  = tk.LabelFrame(left_frame, text="Rate Meter",
        foreground="black", padx=5, pady=5)
    rate_frame.grid(row=2, column=0, sticky=tk.W+tk.E+tk.N)

    ratefig = Figure(figsize=(3, 2), dpi=100)
    t = np.arange(0, 3, .01)
    ratefig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))
    canvas = FigureCanvasTkAgg(ratefig, master=rate_frame) # A tk.DrawingArea.
    canvas.draw()
    canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.W+tk.E+tk.N)


    histogram_frame = tk.LabelFrame(right_frame, text="Muon Decay " +
        "Time Histogram", foreground="black", padx=5, pady=5)
    histogram_frame.grid(row=0, column=0, sticky=tk.NW)
    linlog_button = tk.Button(histogram_frame,  text="Change " +
        "y-scale Linear/Log", foreground="black", width=20)
    linlog_button.grid(row=0, column=0, sticky=tk.W)
    export_button = tk.Button(histogram_frame,  text="Export " +
        "Histogram", foreground="black",
        width=20)
    export_button.grid(row=0, column=1, sticky=tk.E)

    fig = Figure(figsize=(5, 4), dpi=100)
    t = np.arange(0, 3, .01)
    fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))
    canvas = FigureCanvasTkAgg(fig, master=histogram_frame)  # A tk.DrawingArea.
    canvas.draw()
    canvas.get_tk_widget().grid(row=1, column=0, columnspan=2,
        sticky=tk.W+tk.E+tk.N)

    detector_frame = tk.LabelFrame(right_frame, text="Muons " +
        "Through Detector", foreground="black", width=400,
        height=100, padx=5, pady=5)
    detector_frame.grid(row=1, column=0, sticky=tk.W+tk.E+tk.N)

    master.mainloop()
        
    

if __name__ == '__main__':
    muon_GUI()
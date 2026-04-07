#! /usr/bin/env python

import argparse
import re
import os      
import sys
import numpy as np
import queue
import serial
import threading
import time
import tkinter as tk
import tkinter.filedialog as filedialog

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from serial.tools.list_ports import comports
from tkinter import messagebox
from collections import deque

# Import functions needed to fit data
from lmfit.models import ExponentialModel, ConstantModel
# Need Statistical distributions (Student T and Chi square)
import scipy.stats as stats 
import pandas as pd

from Muon.detect import detect_queue

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()  # configure root handler


class MuonApp:
    def __init__(self, root, q):
        self.root = root
        self.root.protocol('WM_DELETE_WINDOW', self.confirm_quit)
        # Define detection parameters
        self.outfname = 'muon_data.txt'
        self.appnd = tk.BooleanVar()
        self.appnd.set(False)
        
        self.port = ("/dev/null")
        self.nbins = 20
        self.sampletime = 30
        self.ndecays = 0
        
        self.q = q
        self.paused = False
        self.data = deque()
        self.control_q = queue.Queue()
        self.config_win = None
        # Figure for histogram
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Muon Decay Times")
        self.ax.set_ylim([0, 20])
        self.ax.set_xlabel(r'Time ($\mu$s)')
        self.ax.set_ylabel('Counts')
        self.bins = np.arange(0, 21, 1)
        self.tt = (bins[1:] + bins[0:-1]) / 2
        self.counts = np.array([], dtype=int)
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()
        controls = tk.Frame(root)
        controls.pack(pady=5)
        self.configbutton = tk.Button(controls, text="Configure",
            command=self.configure)
        self.configbutton.pack(side=tk.LEFT, padx=5)
        self.startbutton = tk.Button(controls, text="Start",
            command=self.collect)
        self.startbutton.pack(side=tk.LEFT, padx=5)
        self.fitbutton = tk.Button(controls, text='Fit',
            command=self.fit, state='disabled')
        self.fitbutton.pack(side=tk.LEFT, padx=5)
        self.savefigbutton(controls, text='Save Histogram',
            command=self.savefig, state='disabled')
        self.quitbutton = tk.Button(controls, text="Quit",
            command=self.confirm_quit)
        self.quitbutton.pack(side=tk.RIGHT, padx=5)
        self.update_histogram()
    
    def configure(self):
        ports = getports()
        self.fname = tk.StringVar()
        self.fname.set(self.outfname)
        try:
            if self.config_win.state() == 'normal':
                self.config_win.focus()
        except:
            self.config_win = tk.Toplevel(self.root)
            self.config_win.title("Configuration")
            self.portname = tk.StringVar()
            self.portname.set(self.port)
            port_frame = tk.LabelFrame(self.config_win, text="Select " +
                "Port", foreground="black")
            port_frame.pack()
            for dv in ports:
                dv_rbutton = tk.Radiobutton(port_frame, text=dv, 
                    foreground="black", variable=self.portname, value=dv)
                dv_rbutton.pack(anchor=tk.W)
            outfile_frame = tk.LabelFrame(self.config_win, text="Output" +
                " File", foreground="black")
            outfile_frame.pack()
            outfile_button = tk.Button(outfile_frame, text="Select" +
                " File", foreground="black", command=self.outfile_dialog)
            outfile_button.grid(row=0, column=0)
            outfile_label = tk.Label(outfile_frame,
                textvariable=self.fname, foreground="black")
            outfile_label.grid(row=0, column=1)
            appnd_check = tk.Checkbutton(outfile_frame, 
                text="Append to File", variable=self.appnd,
                foreground="black")
            appnd_check.grid(row=1, column=1, sticky=tk.E)
            dt_frame = tk.LabelFrame(self.config_win, text="Detect " +
                "Time", foreground="black")
            dt_frame.pack()

            dtchoice_var = tk.IntVar(value=3600)
            dtother_var = tk.StringVar()

            def dton_choice_change():
                if dtchoice_var.get() == -1:
                    dtother_entry.config(state="normal")
                    dtother_entry.focus()
                else:
                    dtother_entry.config(state="disabled")
                    dtother_var.set("")            
            
            dttext = ['1 h', '1 d', '2 d', '7 d']
            dtvals = [3600, 24 * 3600, 2 * 24 * 3600, 7 * 24 * 3600]

            for n in range(len(dtvals)):
                tk.Radiobutton(dt_frame, text=dttext[n],
                    variable=dtchoice_var, value=dtvals[n],
                    command=dton_choice_change).pack(anchor="w")
            tk.Radiobutton(dt_frame, text="Other:",
                variable=dtchoice_var, value=-1,   
                command=dton_choice_change).pack(anchor="w")
            dtother_entry = tk.Entry(dt_frame,
                textvariable=dtother_var, width=8,   
                state="disabled")
            dtother_entry.pack(anchor="w")
                    
            tk.Button(dt_frame, text='OK', command=lambda:
                self.submitconfig(dtchoice_var,
                dtother_var)).pack(pady=10)
    
    def submitconfig(self, dtchoice_var, dtother_var):
        if dtchoice_var.get() == -1:
            text = dtother_var.get().strip()
            if not text:
                messagebox.showerror("Error", "Please enter a value for 'Other'.")
                return
            try:
                self.sampletime = int(text)
            except ValueError:
                    messagebox.showerror("Invalid input", 
                        f"'{text}' is not a valid integer.")
                    return 
        else:
            self.sampletime = dtchoice_var.get()
        self.port = self.portname.get()
        text = f'port: {self.port}\noutfname: {self.outfname}\nsampletime: {self.sampletime}'
        messagebox.showinfo('Success', text)
        self.config_win.destroy()
            
    def outfile_dialog(self):
        if os.path.dirname(self.outfname):
            idir = os.path.dirname(self.outfname)
        else:
            idir = os.curdir
        self.outfname = filedialog.asksaveasfilename(initialdir=idir,
            initialfile=os.path.basename(self.outfname))
        self.fname.set(os.path.relpath(self.outfname))
        
    def collect(self): 
        self.startbutton.config(text='Pause', command=self.pause)
        threading.Thread(target=detect_queue, args=(self.port,
            self.q, self.control_q), kwargs={'outfile':
            'self.outfname', 'appnd': False, 'sampletime':
            self.sampletime, 'ndecays': self.ndecays},
            daemon=True).start()
          
    def pause(self):
        self.control_q.put('pause')
        self.paused = True
        self.startbutton.config(text='Resume', command=self.resume)
        self.fitbutton.config(state='normal')
        self.savefigbutton.config(state='normal')
    
    def resume(self):
        self.paused = False
        self.control_q.put('resume')
        self.startbutton.config(text='Pause', command=self.pause)
        self.fitbutton.config(state='disabled')
        self.savefigbutton.config(state='disabled')

    def stop(self):
        self.control_q.put('stop')
        self
   
    def update_histogram(self):
        #logger.debug("update_histogram")
        if not self.paused:
            while not self.q.empty():
                newdecays = self.q.get()
                self.data.extend(newdecays)
                logger.debug('Data from q') 
                logger.debug(f'newdecays: {newdecays}; data: {self.data}')
            self.ax.clear()
            self.bincounts, _, _ = self.ax.hist(self.data,
                bins=self.bins, edgecolor="black", label='Data')
            self.ax.set_title("Muon Decay Times")
            self.ax.set_xlabel(r'Time ($\mu$s)')
            self.ax.set_ylabel('Counts')

            self.canvas.draw_idle()

        self.root.after(100, self.update_histogram)
    
    def fit(self):
        muondecay = ExponentialModel()
        bg = ConstantModel()
        model = muondecay + bg
        init = bg.make_params(c=self.bincounts[-1])
        init += muon.make_params(amplitude=100, decay=1.67)
        nlm = model.fit(self.bincounts, init, x=self.tt)
        fit = nlm.eval(x=tt)
        dcount = nlm.eval_uncertainty(sigma=0.95)
        self.ax.plot(tt, fit, '-k', lw=2, label='Fit')
        self.ax.plot(tt, fit+dcount, '--k', label='95% confidence band')
        self.ax.plot(tt, fit-dcount, '--k')
        self.ax.legend()
        a = nlm.params['c'].value
        n0 = nlm.params['amplitude'].value
        tau = nlm.params['decay'].value
        delta_a = nlm.params['c'].stderr
        delta_n0 = nlm.params['amplitude'].stderr
        delta_tau = nlm.params['decay'].stderr
        t_a = a / delta_a
        t_n0 = n0 / delta_n0
        t_tau = tau / delta_tau
        tdof = data.Counts.size - 3
        p_a = 2 * (1 - stats.t.cdf(t_a, tdof))
        p_n0 = 2 * (1 - stats.t.cdf(t_n0, tdof))
        p_tau = 2 * (1 - stats.t.cdf(t_tau, tdof))
        fitparams = pd.DataFrame({
            'Estimate': [a, n0, tau], 
            'Std Error': [
                nlm.params['c'].stderr,
                nlm.params['amplitude'].stderr,
                nlm.params['decay'].stderr
            ], 
            'T Value': [t_a, t_n0, t_tau], 
            'DOF': [tdof, tdof, tdof], 
            'P(>|T|)': [p_a, p_n0, p_tau]
        }, index=['a', 'n0', 'tau'])
        

    def confirm_quit(self):
        if tk.messagebox.askokcancel('Quit', 'Do you really want to quit?'):
            self.root.destroy()

def getports():
    """Returns an array of available ports with the ports containing
    'USB' in their name at the front of the array.
    """
    ports = comports()
    devs = []
    for port in ports:
        devs = devs + [port.device]
    pattern = r'USB'
    usbdevs = [dev for dev in devs if re.search(pattern, dev)]
    if len(usbdevs) == 0:
        return devs
    return usbdevs
    
logger.debug("Starting")
root = tk.Tk()
root.title("Muon Decay Monitor")

q = queue.Queue()    
MuonApp(root, q)
root.mainloop()

        
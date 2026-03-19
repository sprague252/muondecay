import os
from platform import system as sys
from subprocess import Popen, STDOUT
import time
import tkinter as tk
import tkinter.filedialog as filedialog

from IPython.display import display, clear_output, update_display
import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
from serial.tools.list_ports import comports


class controlpanel:

    def __panelname__(self, pname, stack=[]):
        if pname == 'port':
            stack = stack + [self.port]
        elif pname == 'path':
            stack = stack + [self.path] 
        elif pname == 'file':
            stack = stack + [self.filebox]
        elif pname == 'etime':
            stack = stack + [self.etimebox]
        elif pname == 'nmuon':
            stack = stack + [self.nmuon]
        return stack


    def __init__(self, inputs=['port', 'fname', 'etime', 'nmuon']):
        style = {'description_width': 'initial'}
        devs = getports()
        self.port = widgets.RadioButtons(
            options=devs,
            description='Select Port:',
            disabled=False
        )
        self.path = widgets.Text(
            value='',
            placeholder='FilePath',
            description='Output Path:',
            disabled=False
        )
        self.file = widgets.Text(
            value='muon.txt',
            placeholder='Filename',
            description='Output File:',
            disabled=False,
            layout=widgets.Layout(margin_right='0px')
        )
        self.append = widgets.Checkbox(
            value=False,
            description='Append',
            disabled=False,
            layout=widgets.Layout(margin_left='0px')
        )
        self.filebox = widgets.HBox(
            [self.file, self.append]
        )
        self.etime = widgets.FloatText(
            value=7.0,
            description='Elaped Time:',
            style=style,
            disabled=False
        )
        self.tunit = widgets.Dropdown(
            options=[('s', 1), ('h', 3600), ('d', 86400)],
            value=86400,
            description='Unit:',
            layout=widgets.Layout(width='9em'),
        )
        self.etimebox = widgets.HBox([self.etime, self.tunit])
        self.nmuon = widgets.IntText(
            value=0,
            description='Number of Muons:',
            style=style
        )
        stack = []
        for input in inputs:
            stack = self.__panelname__(input, stack)
        self = widgets.VBox(stack)
        display(self)

    def fdialog(self):
        
        def opendialog(parent, fpath, fname):
            if sys() == 'Darwin':  # How Mac OS X is identified by Python
                os.system('/usr/bin/osascript -e ' + 
                    '\'tell app "Finder" to set frontmost of process ' +
                    '"python" to true\'')
            fout = filedialog.asksaveasfilename(parent=parent, initialdir=fpath, 
                initialfile=fname)
            return fout
        
        root = tk.Tk()
        root.withdraw()
        if self.path.value:
            fullpath = self.path.value + '/' + self.file.value
        else:
            fullpath = './' + self.file.value
        fname = os.path.basename(fullpath)
        fpath = os.path.dirname(fullpath)
        if fpath == '':
            fpath = os.curdir
        fout =  opendialog(root, fpath, fname)
        if fout:
            self.path.value = os.path.dirname(fout)
            self.file.value = os.path.basename(fout)
            root.destroy()

def getports():
    ports = comports()
    devs = []
    for port in ports:
        devs = devs + [port.device]
    return devs

def deltaports():
    devs0 = getports()
    print('Serial ports scanned ...')
    input('Connect new device. Then press any key ...')
    devs1 = getports()
    newdev = np.setdiff1d(devs1, devs0)
    return newdev.tolist()

def detect_spawn(port, outfile='muondata.txt', appnd=False, sampletime=0,
    ndecays=0):
    if appnd:
        proc = Popen(['python', '-m', 'Muon.detect', '-a', '-n',
            str(ndecays), '-t', str(sampletime), '-o', outfile, port])
    else:
        proc = Popen(['python', '-m', 'Muon.detect', '-n', str(ndecays),
            '-t', str(sampletime), '-o', outfile, port])
    return proc

def detect_monitor(fname='muon_data.txt', hgrange=[0, 20]):
    
    def follow(thefile):
    #    thefile.seek(0,2)
        while True:
            line = thefile.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line
    
    def hgplot(fig, ax, times):
        hist, bin_edge, _ = ax.hist(times, bins = 20, range = hgrange, 
           edgecolor='black', facecolor='0.85')
        ax.set_xlabel(r'Time ($\mu$s)')
        ax.set_ylabel('Counts')
        ax.set_xlim([0, 20])
#        clear_output(wait=True)
#        update_display(display_id='decay plot', obj=fig)
        plt.pause(0.0001)
        clear_output(wait=True)

        #       fig.canvas.draw()
        #plt.draw()
        #plt.pause(0.0001)
        #clear_output(wait=True)

    def killit():
        global running
        running = False
    
    global running
    running = True
#    plt.ion()
#    plt.ioff()
#    out = widgets.Output()
    times = np.array([])
    with open(fname, "r") as datafile:
        partial = ''
        for line in datafile:
            if line[-1] == '\n':
                data = np.fromstring(partial + line, sep=' ')
                partial = ''
                if int(data[0]) < 40000:
                    times = np.append(times, [int(data[0])/1000.])
            else:
                partial = line
        fig, ax = plt.subplots()
#        display(fig, display_id='decay plot')
        hgplot(fig, ax, times)
        datalines = follow(datafile)
#         update_display(display_id='decay plot', obj=fig)
#         plt.pause(0.0001)
        clear_output(wait=True)
#        out.clear_output(wait=True)
        for line in datalines:
            if line == '-999' or running == False:
                return times
            if line[-1] == '\n':
                data = np.fromstring(partial + line, sep=' ')
                partial = ''
                if int(data[0]) < 40000:
                    times = np.append(times, [int(data[0])/1000.])
                    fig, ax = plt.subplots()
                    hgplot(fig, ax, times)
#                    update_display(display_id='decay plot', obj=fig)
#                    fig.canvas.draw_idle()
#                    out.clear_output()
#                    out.append_display_data(fig)
#                     plt.pause(0.0001)
#                     clear_output(wait=True)
#                    out.clear_output(wait=True)
            else:
                partial = line

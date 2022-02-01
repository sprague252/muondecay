from __future__ import print_function, division
import os
import ipywidgets as widgets
from serial.tools.list_ports import comports
import numpy as np
import matplotlib.pyplot as plt
import tkinter.filedialog as filedialog
import tkinter as tk
from platform import system as sys


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
            from platform import system as sys
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
    from subprocess import Popen, STDOUT
    if appnd:
        proc = Popen(['python', '-m', 'Muon.detect', '-a', '-n',
            str(ndecays), '-t', str(sampletime), '-o', outfile, port])
    else:
        proc = Popen(['python', '-m', 'Muon.detect', '-n', str(ndecays),
            '-t', str(sampletime), '-o', outfile, port])
    return proc

def detect_monitor(fname='muon_data.txt', hgrange=[0, 20], mtime=60.):
    import matplotlib.pyplot as plt
    from IPython.display import display, clear_output
    import time
    from matplotlib.widgets import Button
    
    def follow(thefile, nnloop=600):
    #    thefile.seek(0,2)
        nloop = 0
        while nloop < nnloop:
            line = thefile.readline()
            if not line:
                time.sleep(0.1)
                nloop += 1
                continue
            yield line
        line = '-999'
        yield line
    
    def hgplot(fig, ax, times, clearout=True):
        hist, bin_edge, _ = ax.hist(times, bins = 20, range = hgrange, 
           edgecolor='black', facecolor='0.85')
        ax.set_xlabel(r'Time ($\mu$s)')
        ax.set_ylabel('Counts')
        ax.set_xlim([0, 20])
        #       fig.canvas.draw()
        plt.draw()
        plt.pause(0.0001)
        if clearout: 
            clear_output(wait=True)
    
    global running
    running = True
    plt.ion()
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
        hgplot(fig, ax, times)
#         bax = plt.axes([0.8, -0.05, 0.1, 0.075])
#         plt.draw()
#         plt.pause(0.0001)
#         clear_output(wait=True)
        datalines = follow(datafile, nnloop=10*mtime)
        for line in datalines:
            if line == '-999':
                fig, ax = plt.subplots()
                hgplot(fig, ax, times, clearout=False)
                print('Monitor period {:g} s ended.'.format(mtime) +
                    '  Run again to continue monitoring.')
                return times
            if line[-1] == '\n':
                data = np.fromstring(partial + line, sep=' ')
                partial = ''
                if int(data[0]) < 40000:
                    times = np.append(times, [int(data[0])/1000.])
#                     clear_output()
                    fig, ax = plt.subplots()
                    hgplot(fig, ax, times)
#                     bax = plt.axes([0.8, -0.05, 0.1, 0.075])
#                     stopit = Button(bax, 'Stop')
#                     stopit.on_clicked(killit)
#                     plt.draw()
#                     plt.pause(0.0001)
#                     clear_output(wait=True)
            else:
                partial = line

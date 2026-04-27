import os
import ipywidgets as widgets
import tkinter as tk
import tkinter.filedialog as filedialog
from platform import system as sys
from subprocess import Popen, STDOUT
import time

from IPython.display import display, clear_output
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from serial.tools.list_ports import comports

from muondecay.detect import detect

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
    """Returns an array of available ports with the ports containing
    'USB' in their name at the front of the array.
    """
    ports = comports()
    devs = []
    for port in ports:
        devs = devs + [port.device]
    sorted_devs = sorted(devs, key=_USB_sort_key)
    return sorted_devs

def _USB_sort_key(item):
    """Sort function to prioritize items with 'USB' in the name.
    """
    has_USB = 'USB' in item
    return (not has_USB, item)

def deltaports():
    """A helper function to find the port associated with the muon
    detector. Execute the function with the USB cable disconnected,
    and follow the instructions in the prompt about connecting the
    cable. The function identifies the new port and returns its name.
    """
    devs0 = getports()
    print('Serial ports scanned ...')
    input('Connect new device. Then press any key ...')
    devs1 = getports()
    newdev = np.setdiff1d(devs1, devs0)
    return newdev.tolist()

def detect_spawn(port, outfile='muondata.txt', appnd=False, sampletime=0,
    ndecays=0):
    """Open a background process running the detect function. The 
    process will detect muon events and record them to a file, which
    can be monitored.
    
    USAGE
    
    proc = detect_spawn(port[, outfile='muondata.txt', appnd=False, 
        sampletime=0, ndecays=0])
        
    PARAMETERS
    
    port: serial port (device) connected to the muon detector
    outfile: name of the output file (default: muondata.txt)
    appnd: append data to the output file if it exists (otherwise the
        file is overwritten)
    sampletime: Clock time (seconds) for which the data should be
        collected. A value of 0 results in a limit of 1 week (604800 s).
        (default: 0)
    ndecays: target number of muon decays (0 for no target). Program
        ends once the target is met or exceeded. (default: 0)
    
    RETURNS
    
    proc: Process handle returned by subprocess.Popen
    """
    if appnd:
        proc = Popen(['python', '-m', 'Muon.detect', '-a', '-n',
            str(ndecays), '-t', str(sampletime), '-o', outfile, port])
    else:
        proc = Popen(['python', '-m', 'Muon.detect', '-n', str(ndecays),
            '-t', str(sampletime), '-o', outfile, port])
    return proc

def detect_monitor(fname='muon_data.txt', hgrange=[0, 20], mtime=60.):
    """
    Monitor the data file, plotting a decay histogram and updating the 
    plot with new detections.
    
    USAGE
    
    detect_monitor([fname='muon_data.txt', hgrange=[0, 20], mtime=60.])
    
    PARAMETERS
    
    fname: Optional data file name to monitor. (default: 'muon_data.txt')
    hgrange: Optional range for histogram times. (default: [0, 20])
    mtime: Optional time in seconds to monitor the file. (default: 60)
    """
    
    def _follow(thefile, nnloop=600):
        # Get new lines in thefile using yield
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
    
    def _hgplot(fig, ax, times, clearout=True):
        # Plot decay histogram
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
        _hgplot(fig, ax, times)
#         bax = plt.axes([0.8, -0.05, 0.1, 0.075])
#         plt.draw()
#         plt.pause(0.0001)
#         clear_output(wait=True)
        datalines = _follow(datafile, nnloop=10*mtime)
        for line in datalines:
            if line == '-999':
                fig, ax = plt.subplots()
                _hgplot(fig, ax, times, clearout=False)
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
                    _hgplot(fig, ax, times)
#                     bax = plt.axes([0.8, -0.05, 0.1, 0.075])
#                     stopit = Button(bax, 'Stop')
#                     stopit.on_clicked(killit)
#                     plt.draw()
#                     plt.pause(0.0001)
#                     clear_output(wait=True)
            else:
                partial = line

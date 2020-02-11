import os
import ipywidgets as widgets
from serial.tools.list_ports import comports
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display
import tkinter.filedialog as filedialog
import tkinter as tk
from platform import system as platform


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
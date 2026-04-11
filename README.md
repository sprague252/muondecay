# Muon

This is Python module to read and analyze data from TeachSpin's muon
decay apparatus.

Version 0.1

# Modules 

* analysis - contains functions to analyze muon decay data with a 
nonlinear fit and with a chi-squared test.

* detect - contains a function to read serial data from the muon
detector and write the decay information to a data file and another
function that also writes decay data to a queue that can be read by the
GUI. This module can be run on the command line as a standalone muon
detection function.

* muonGUI - a GUI interface to the muon detection functions.

* MuonJupyter - a collection of functions to run muon detection from
Jupyter Lab (or Jupyter Notebook).
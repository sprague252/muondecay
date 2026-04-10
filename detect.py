#!/usr/bin/env python
"""This module provides the detect function to detect muon decays with
TeachSpin's muon decay apparatus.  The module may be called from the
command line by name with "detect.py [args]" or with "python -m
Muon.detect [args]". The detect function can be called from within
Python. Execute "detect.py --help" from the command line for a complete
help message with command-line arguments or "help(detect.detect)" from
within IPython (Jupyter) for a complete docstring of the detect
function.
"""
import re
import time
import sys
import time
import argparse
from os import fsync
import queue

import numpy as np
import serial

import logging


def detect(port, outfile='muondata.txt', appnd=False, sampletime=0,
    ndecays=0, killswitch=None):
    """Capture the output from TeachSpin's muon decay apparatus and save
    the results to an output file with the same format as the original
    'muon_detect.tcl' program provided by TeachSpin.
    
    USAGE
    
    muon_count, decay_count, etime = detect(port,
        outfile='muondata.txt', fmode='w', sampletime=0, ndecays=0,
        killswitch=None)

    PARAMETERS
    
    port: serial port (device) connected to the muon detector
    outfile: name of the output file (default: muon_data.txt)
    appnd: append data to the output file if it exists (otherwise the
        file is overwritten)
    sampletime: Clock time (seconds) for which the data should be
        collected. A value of 0 results in a limit of 1 week (604800 s).
        (default: 0)
    ndecays: target number of muon decays (0 for no target). Program
        ends once the target is met or exceeded. (default: 0)
    killswitch: a parameter to stop execution. If defined as a
        multiprocessing.Value object, setting of killswitch.value = 0 in
        another process will stop execution. This parameter is ignored
        if killswitch is None. (default: None)
    
    RETURNS
    
    muon_count: total number of muons passing through the detector
        during execution. Note that if the data are appended to a file,
        the file may contain additional muon counts.
    decay_count: total number of muons decays detected during execution.
        Note that if the data are appended to a file, the file may
        contain additional muon decays.
    etime: The total sampling time during execution. Note that if the
        data are appended to a file, this time does not include the time
        for any previous samples.
    """
    if appnd:
        fmode = 'a'
    else:
        fmode = 'w'
    if ndecays == 0:
        ndecays = 1000000 # Default maximum number of decays
    if sampletime == 0:
        sampletime = 7 * 24 * 3600 # Default maximum sample time 1 week
    reading = True
    decay_count = 0
    muon_count = 0
    # Define the regex substitution string to eliminate groups of less
    # than three characters.
    ex_3_digit = b'^[\\dA-E]{1,2}\r|\n[\\dA-E]{1,2}\r|\n[\\dA-E]{1,2}\r?$'
    # Define the regex substitution string to eliminate return and
    # newline characters.
    ex_cr_newline = b'\r\n*|\n'
    with open(outfile, fmode) as output:
        detector = serial.Serial(port, baudrate=115200, timeout=1)
        t0 = time.time()
        while reading:
            rawdata=detector.read(1024)
            tstamp = time.time()
            # The following command first eliminates samples that do not
            # contain three digits and then eliminates the return and
            # newline characters of the result.
            datab = re.sub(
                ex_cr_newline, 
                b'', 
                re.sub(ex_3_digit, b'', rawdata)
            )
            try:
                data0x = np.frombuffer(datab, dtype='|S3')
            except ValueError:
                print('ValueError occurred reading |S3 ...', file=sys.stderr)
                rdf = open('rawdata_error' + str(int(tstamp)), 'bw')
                rdf.write(rawdata)
                rdf.close()
                print('rawdata written to file rawdata_error' + str(int(tstamp)),
                    file=sys.stderr)
                print('Data not saved ...', file=sys.stderr)
            data_ns = np.array([20 * int(n, 16) for n in data0x])
            muon_count += data_ns.size
            decay_count += data_ns[data_ns < 20000].size
            timeouts = np.flip(np.argwhere(data_ns==20000).flatten())
            if timeouts.size > 0:
                prev = timeouts[0]
                count = 1
                indlist = np.array([], dtype=np.int64)
                countlist = np.array([], dtype=np.int64)
                for val in timeouts[1:]:
                    if val == prev - 1:
                        count += 1
                    else:
                        indlist = np.insert(indlist, 0, prev)
                        if count == 1:
                            countlist = np.insert(countlist, 0, 40000)
                        else:
                            countlist = np.insert(countlist, 0, 40000+count)
                        count = 1
                    prev = val
                indlist = np.insert(indlist, 0, prev)
                if count == 1:
                    countlist = np.insert(countlist, 0, 40000)
                else:
                    countlist = np.insert(countlist, 0, 40000+count)            
                data_ns[indlist] = countlist
                data_ns = data_ns[data_ns != 20000]
            data_out = (np.concatenate(([data_ns], 
                [tstamp * np.ones(data_ns.size, dtype=np.int64)]), axis=0).T)
            np.savetxt(output, data_out, fmt='%d')
            output.flush()
            fsync(output.fileno())
            etime = tstamp - t0
            if decay_count >= ndecays or etime >= sampletime:
                reading = False
            if killswitch:
                if killswitch.value == False:
                    reading = False
    return muon_count, decay_count, etime

def detect_queue(port, data_queue, control_queue,
    outfile='muondata.txt', appnd=False, sampletime=0,
    ndecays=0, killswitch=None):
    """Capture the output from TeachSpin's muon decay apparatus and save
    the results to an output file with the same format as the original
    'muon_detect.tcl' program provided by TeachSpin. This version writes
    decay data to a queue that can be read by another thread.
    
    USAGE
    
    detect_queue(port, data_queue,
        outfile='muondata.txt', fmode='w', sampletime=0, ndecays=0,
        killswitch=None)

    PARAMETERS
    
    port: serial port (device) connected to the muon detector
    data_queue: a queue.Queue object for writing the decay data.
    outfile: name of the output file (default: muon_data.txt)
    appnd: append data to the output file if it exists (otherwise the
        file is overwritten)
    sampletime: Clock time (seconds) for which the data should be
        collected. A value of 0 results in a limit of 1 week (604800 s).
        (default: 0)
    ndecays: target number of muon decays (0 for no target). Program
        ends once the target is met or exceeded. (default: 0)
    killswitch: a parameter to stop execution. If defined as a
        multiprocessing.Value object, setting of killswitch.value = 0 in
        another process will stop execution. This parameter is ignored
        if killswitch is None. (default: None)
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logging.basicConfig()  # configure root handler
    logger.debug('Started detect_queue')
    if appnd:
        fmode = 'a'
    else:
        fmode = 'w'
    if ndecays == 0:
        # Default maximum number of decays (a lot)
        ndecays = 100000000 
    if sampletime == 0:
        # Default maximum sample time 10^8 s (31.7 years), meaning it
        # will run until the parent process quits or kills it.
        sampletime = 100000000 
    running = True
    paused = False
    decay_count = 0
    muon_count = 0
    # Define the regex substitution string to eliminate groups of less
    # than three characters.
    ex_3_digit = b'^[\\dA-E]{1,2}\r|\n[\\dA-E]{1,2}\r|\n[\\dA-E]{1,2}\r?$'
    # Define the regex substitution string to eliminate return and
    # newline characters.
    ex_cr_newline = b'\r\n*|\n'
    with open(outfile, fmode) as output:
        detector = serial.Serial(port, baudrate=115200, timeout=1)
        t0 = time.time()
        tstamp = t0
        while running:
            # See if we are paused or stopped
            try:
                cmd = control_queue.get_nowait()
                if cmd == 'pause':
                    paused = True
                elif cmd == 'resume':
                    paused == False
                elif cmd == 'stop':
                    running = False
            except queue.Empty:
                pass
            if paused:
                time.sleep(0.1)
                continue
            rawdata=detector.read(1024)
            # The following command first eliminates samples that do not
            # contain three digits and then eliminates the return and
            # newline characters of the result.
            datab = re.sub(
                ex_cr_newline, 
                b'', 
                re.sub(ex_3_digit, b'', rawdata)
            )
            tstamp = time.time()
            try:
                data0x = np.frombuffer(datab, dtype='|S3')
            except ValueError:
                print('ValueError occurred reading |S3 ...', file=sys.stderr)
                rdf = open('rawdata_error' + str(int(tstamp)), 'bw')
                rdf.write(rawdata)
                rdf.close()
                print('rawdata written to file rawdata_error' + str(int(tstamp)),
                    file=sys.stderr)
                print('Data not saved ...', file=sys.stderr)
            data_ns = np.array([20 * int(n, 16) for n in data0x])
            muon_count += data_ns.size
            # Make an array of only decays and put it in the queue.
            decays = data_ns[data_ns < 20000] / 1000
            decay_count += decays.size
            if decays.size > 0:
                rate = muon_count / (tstamp - lasttime)
                data_queue.put((decays, rate))
                lasttime = tstamp
                muon_count = 0
            timeouts = np.flip(np.argwhere(data_ns==20000).flatten())
            if timeouts.size > 0:
                prev = timeouts[0]
                count = 1
                indlist = np.array([], dtype=np.int64)
                countlist = np.array([], dtype=np.int64)
                for val in timeouts[1:]:
                    if val == prev - 1:
                        count += 1
                    else:
                        indlist = np.insert(indlist, 0, prev)
                        if count == 1:
                            countlist = np.insert(countlist, 0, 40000)
                        else:
                            countlist = np.insert(countlist, 0, 40000+count)
                        count = 1
                    prev = val
                indlist = np.insert(indlist, 0, prev)
                if count == 1:
                    countlist = np.insert(countlist, 0, 40000)
                else:
                    countlist = np.insert(countlist, 0, 40000+count)            
                data_ns[indlist] = countlist
                data_ns = data_ns[data_ns != 20000]
            data_out = (np.concatenate(([data_ns], 
                [tstamp * np.ones(data_ns.size, dtype=np.int64)]), axis=0).T)
            np.savetxt(output, data_out, fmt='%d')
            output.flush()
            fsync(output.fileno())
            etime = tstamp - t0
            if decay_count >= ndecays or (sampletime > 0 and etime >=
                sampletime):
                reading = False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 
        ('Acquire data from the TeachSpin muon decay apparatus.'))
    parser.add_argument('-a', '--append', action='store_true',
        help='append data to the output file if it exists ' +
        '(otherwise the file is overwritten)')
    parser.add_argument('-n', '--ndecays', type=int, default=0, 
        help='target number of muon decays (0 for no target)')
    parser.add_argument('-o', '--outfile', default='muon_data.txt',
        help='name of the output file (default: muon_data.txt)')
    parser.add_argument('-s', '--summarize', action='store_true',
        help='at completion print a summary of the total muons detected, ' +
        'decays detected and sampling time to STDOUT')
    parser.add_argument('-t', '--sampletime', type=int, default=0, 
        help='Clock time (seconds) for which the data should be collected ' +
        '(0 for default limit, 1 week)')
    parser.add_argument('port', 
        help='serial port (device) connected to the muon detector')
    args = parser.parse_args()

    muon_count, decay_count, etime = detect(args.port,
        outfile=args.outfile, appnd=args.append,
        sampletime=args.sampletime, ndecays=args.ndecays)
    
    if args.summarize:
        print('Muons detected: ', muon_count)
        print('Decays detected: ', decay_count)
        print('Sampling time (s): ', etime)

    sys.exit(0)

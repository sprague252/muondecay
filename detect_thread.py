import argparse
import re
import numpy as np
import serial
import threading
import queue
import sys
import time
from os import fsync


def detect_reader(port, baudrate, data_queue):
    with serial.Serial(port, baudrate=baudrate, timeout=1) as ser:
        buffer = b''
        while True:
            if ser.in_waiting > 0:
                new_data = ser.read(ser.in_waiting)
                buffer += new_data
                while b"\n" in buffer:
                    line_bytes, buffer = buffer.split(b'\n', 1)
                    # Put decoded line into queue
                    data_queue.put(line_bytes)
            else:
                time.sleep(0.01) # Allow CPU to do other things.

def retrieve_from_queue(data_queue):
    """Yields lines from queue."""
    while True:
        yield data_queue.get()
        
def detect_thread(port, outfile='muondata.txt', baudrate=115200, appnd=False, sampletime=0, ndecays=0):
    if appnd:
        fmode = 'a'
    else:
        fmode = 'w'
    reading = True
    line_queue = queue.Queue()
    if ndecays == 0:
        ndecays = 1000000 # Default maximum number of decays
    if sampletime == 0:
        sampletime = 7 * 24 * 3600 # Default maximum sample time 1 week

    decay_count = 0
    muon_count = 0
    # Define the regex substitution string to eliminate groups of less
    # than three characters.
    ex_3_digit = b'^[\\dA-E]{1,2}\r|\n[\\dA-E]{1,2}\r|\n[\\dA-E]{1,2}\r?$'
    # Define the regex substitution string to eliminate return and
    # newline characters.
    ex_cr_newline = b'\r\n*|\n'

    t0 = time.time()
    # Start reader thread.
    t = threading.Thread(target=detect_reader, args=(port, baudrate, line_queue))
    t.daemon = True
    t.start()
    with open(outfile, fmode) as output:
        for line in retrieve_from_queue(line_queue):
            tstamp = time.time()
            # The following command first eliminates samples that do not
            # contain three digits and then eliminates the return and
            # newline characters of the result.
            datab = re.sub(
                ex_cr_newline, 
                b'', 
                re.sub(ex_3_digit, b'', line)
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
                break
    return muon_count, decay_count, etime

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

    muon_count, decay_count, etime = detect_thread(args.port,
        outfile=args.outfile, appnd=args.append,
        sampletime=args.sampletime, ndecays=args.ndecays)
    
    if args.summarize:
        print('Muons detected: ', muon_count)
        print('Decays detected: ', decay_count)
        print('Sampling time (s): ', etime)

    sys.exit(0)


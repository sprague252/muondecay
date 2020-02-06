from __future__ import division, print_function

def detect(port, outfile='muondata.txt', fmode='w', sampletime=0, ndecays=0, 
    killswitch=None):
    import numpy as np
    import re
    import serial
    import time
    import sys
    from os import fsync
    if ndecays == 0:
        ndecays = 1000000 # Default maximum number of decays
    if sampletime == 0:
        sampletime = 14 * 24 * 3600 # Default maximum sample time 2 weeks
    reading = True
    decay_count = 0
    muon_count = 0
    # Define the regex substitution string to eliminate groups of less
    # than three characters.
    ex_3_digit = b'^[\dA-E]{1,2}\r|\n[\dA-E]{1,2}\r|\n[\dA-E]{1,2}\r?$'
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
            prev = timeouts[0]
            count = 1
            indlist = np.array([], dtype=np.int)
            countlist = np.array([], dtype=np.int)
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
                [tstamp * np.ones(data_ns.size, dtype=np.int)]), axis=0).T)
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
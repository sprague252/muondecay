from __future__ import division, print_function

def detect(port, outfile='muondata.txt', fmode='w', sampletime=0, ndecays=0, 
    killswitch=None):
    import numpy as np
    import re
    import serial
    import time
    if ndecays == 0:
        ndecays = 1000000 # Default maximum number of decays
    if sampletime == 0:
        sampletime = 14 * 24 * 3600 # Default maximum sample time 2 weeks
    reading = True
    decay_count = 0
    muon_count = 0
    with open(outfile, fmode) as output:
        detector = serial.Serial(port, baudrate=115200, timeout=1)
        t0 = time.time()
        while reading:
            rawdata=detector.read(1024)
            tstamp = time.time()
            data0x = np.frombuffer(re.sub(b'\r\n*', b'', rawdata), dtype='|S3')
            data_ns = np.array([20 * int(n, 16) for n in data0x])
            muon_count += data_ns.size
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
            data_out = (np.concatenate(([data_ns], 
                [tstamp * np.ones(data_ns.size, dtype=np.int)]), axis=0).T)
            np.savetxt(output, data_out, fmt='%d')
            decay_count += (data_ns < 20000).size
            etime = tstamp - t0
            if decay_count >= ndecays or etime >= sampletime:
                reading = False
            if killswitch:
                if killswitch.value == False:
                    reading = False
    return muon_count, decay_count, etime
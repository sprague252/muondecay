from __future__ import division, print_function

def detect(port, outfile='muondata.txt', fmode='w')
    import numpy as np
    import re
    import serial
    import time
    reading = True
    with open(outfile, fmode) as output:
        detector = serial.Serial(port, baudrate=115200, timeout=1)
        while reading:
            rawdata=detector.read(1024)
            tstamp = 
            data0x = np.frombuffer(re.sub(b'\r\n*', b'', rawdata), dtype='|S3')
            data_ns = np.array([20 * int(n, 16) for n in data0x])
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


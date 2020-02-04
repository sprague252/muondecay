from __future__ import division, print_function

def detect(port, outfile='muondata.txt', appnd=False)
    import numpy as np
    import re
    import serial
    import time
    reading = True
    decay_time = np.array([], dtype=np.int)
    decay_stamp = np.array([], dtype=np.int)
    if appnd=True:
        fmode = 'a'
    else:
        fmode = 'w'
    with open(outfile,fmode) as output:
        detector = serial.Serial(port, baudrate=115200, timeout=1)
        while reading:
            rawdata=detector.read(1024)
            data0x = np.frombuffer(re.sub(b'\r\n*', b'', rawdata), dtype='|S3')
            data_ns = np.array([20 * int(n, 16) for n in data0x])
            


def island_cumsum_vectorized(a):
    """Vectorized function to count consecutive zeros in a numpy array. Taken from 
    https://stackoverflow.com/questions/42129021/counting-consecutive-1s-in-numpy-array
    """
    a_ext = np.concatenate(( [0], a, [0] ))
    idx = np.flatnonzero(a_ext[1:] != a_ext[:-1])
    a_ext[1:][idx[1::2]] = idx[::2] - idx[1::2]
    return a_ext.cumsum()[1:-1]
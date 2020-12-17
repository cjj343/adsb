import numpy as np
import matplotlib.pyplot as plt
import data
import detection
import plane
import threading
import queue
import sys
import adsb_constants as adsb
import demod
from pprint import pprint
planes = {'NULL' : {
            'callsign' : '',
            'odd' : '',
            'even': '',
            'position' : (-1,-1),
            'typecode' : -1,
            'time0' : -1,
            'time1' : -1,
            'speed' : -1,
            'angle': -1,
            'vertical_rate' : -1,
            'speed_type' : '',
            'altitude': -1
        }}

def display_detects(detects,stream):
    # Enough for long squitter + preamble
    msgSize = 112*2+len(adsb.PREAMBLE)
    msgs = np.zeros(shape=(len(detects),msgSize))
    for idx,det in enumerate(detects):
        b = det #- len(PREAMBLE)/2
        e = det + 112*2+len(adsb.PREAMBLE)
        msgs[idx] = np.abs(stream[b:e])
    width, height = plt.figaspect(0.3)
    fig = plt.figure(figsize=(width,height))
    plt.imshow(msgs, aspect='auto', cmap="gray")
    plt.ylabel("Incoming messages")
    plt.xlabel("The Received message")
    plt.show()

def process(q,stop_flag):
    while(not stop_flag.is_set()):
        stream = q.get()
        print('Queue: %d'%q.qsize())
        if len(stream) > 0:
            detect = detection.Detection(stream,adsb.NOISE_THRESH,adsb.PREAMBLE,adsb.DET_THRESH)
            detects = detect.detect()
            msgSize = adsb.MSG_BITS*2+adsb.PREAM_LEN
            msgs = np.zeros(shape=(len(detects),msgSize))
            for idx,det in enumerate(detects.keys()):
                b = det 
                e = det + msgSize
                msgs[idx] = np.abs(stream[b:e])
            dmd = demod.Demod(msgs,planes)
            dmd.demod()
        for k,p in planes.items():
            if k != 'NULL':
                pprint(p)

def main(mode):
    if mode == 'collect':
        dat = data.Data(adsb.ADSB_FREQ,adsb.ADSB_SR,'ADSB')
        stream = dat.data_to_file(30)
        detect = detection.Detection(stream,adsb.NOISE_THRESH,adsb.PREAMBLE,adsb.DET_THRESH)
        detects = detect.detect()
        # print(detects)
        msgSize = adsb.MSG_BITS*2+adsb.PREAM_LEN
        msgs = np.zeros(shape=(len(detects),msgSize))
        for idx,det in enumerate(detects.keys()):
            b = det 
            e = det + msgSize
            msgs[idx] = np.abs(stream[b:e])
        dmd = demod.Demod(msgs,planes)
        dmd.demod()
        pprint(planes)


    elif mode == 'test':
        stream = np.load(sys.argv[2])
        detect = detection.Detection(stream,adsb.NOISE_THRESH,adsb.PREAMBLE,adsb.DET_THRESH)
        detects = detect.detect()
        # print(detects)
        msgSize = adsb.MSG_BITS*2+adsb.PREAM_LEN
        msgs = np.zeros(shape=(len(detects),msgSize))
        for idx,det in enumerate(detects.keys()):
            b = det 
            e = det + msgSize
            msgs[idx] = np.abs(stream[b:e])
        dmd = demod.Demod(msgs,planes)
        dmd.demod()
        for k,p in planes.items():
            if k != 'NULL':# and p['flightnum'] != 'UNKNOWN':
                pprint(p)
    else:
        dat = data.Data(adsb.ADSB_FREQ,adsb.ADSB_SR,'ADSB')
        Qin = queue.Queue()
        stop_flag = threading.Event()
        t_sdr_read = threading.Thread(target = dat.data_to_buf, args = (Qin, adsb.SNAP_LEN, stop_flag))
        t_process = threading.Thread(target = process, args = (Qin, stop_flag))
        # start threads
        t_sdr_read.start()
        t_process.start()
        return stop_flag

if __name__ == "__main__":
    mode = 'run'
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    main(mode)
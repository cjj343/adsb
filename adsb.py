import numpy as np
import matplotlib.pyplot as plt
import acquisition

ADSB_FREQ = 1090e6 #Hz
ADSB_SR = 2e6 #MS/s
SNAP_LEN = 1 #seconds

def main():
    acq = acquisition.Acquisition(ADSB_FREQ,ADSB_SR,'ADSB')
    acq.acq_to_file(SNAP_LEN)

if __name__ == "__main__":
    main()
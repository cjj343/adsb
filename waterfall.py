import numpy as np
import matplotlib.pyplot as plt
import time
import radio
import sys
from decimal import Decimal

def main():
    connect = False
    while(not connect):
        try:
            r = radio.Radio()
            connect = True
        except:
            time.sleep(.5)
            print('Connect fail') 
    r.set_sample_rate(2000000)
    r.set_center_frequency(95500000)
    # num_rows = 4096
    # fft_size = 1024
    # waterfall = np.zeros((num_rows,fft_size))
    buf = np.array([0]*1024, np.complex64)
    r.start_receive()
    r.grab_samples(buf)
    # for i in range(1):
    #     print(i)
    #     grab = True
    #     while(grab):
    #         try:
    #             r.grab_samples(buf)
    #             waterfall[i] = buf
    #             grab = False
    #         except:
    #             continue
    r.stop_receive()
    x = buf
    PSD = (np.abs(np.fft.fft(x)/2e6))**2
    PSD_shifted = np.fft.fftshift(PSD)
    PSD_log = 10*np.log10(PSD_shifted)
    
    # PSD = np.abs(np.fft.fft(waterfall[0]))
    # PSD = (PSD/1024)**2
    #PSD_log = 10.0*np.log10(PSD)
    # PSD_shifted = np.fft.fftshift(PSD_log)
    f = np.linspace(2e6/-2.0/1e6, 2e6/2.0/1e6, 1024)
    plt.plot(f, PSD_log)
    plt.xlabel("Frequency [MHz]")
    plt.ylabel("Magnitude [dB]")
    plt.grid(True)
    plt.show()

    # fig, ax = plt.subplots()
    # im = ax.imshow(np.abs(waterfall))
    # plt.show()


if __name__ == "__main__":
    main()
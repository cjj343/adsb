import time
import radio
import numpy as np
import datetime

class Acquisition:
    def __init__(self, freq, sr, tgt):
        self.freq = freq
        self.sr = sr
        self.sd = 1/sr
        self.tgt = tgt
        connect = 5
        while(connect):
            try:
                self.sdr = radio.Radio()
                break
            except Exception, e:
                errorMsg = e
                time.sleep(1)
                connect -= 1
        if connect == 0:
            raise RuntimeError(errorMsg)
        self.sdr.set_sample_rate(self.sr)
        self.sdr.set_center_frequency(self.freq)
    
    def acq_to_file(self,snap,fname=None):
        nsamps = snap/self.sd
        samps = np.array([])
        buf = np.arange(self.sdr.get_buffer_size())
        self.sdr.start_receive()
        while(len(samps) < nsamps):
            try:
                self.sdr.grab_samples(buf)
            except Exception, e:
                print(e)
                continue
            samps = np.append(samps,buf)
        self.sdr.stop_receive()
        dt = datetime.datetime.now().strftime("%Y%m%d_%X")
        if fname == None:
            # TODO: where to save on default
            np.save('%s_%s.npy'%(self.tgt,dt),samps)
        # TODO: save to different location   

    def acq_to_buf(self,snap):
        buf = np.arrange(snap/self.sr)
        self.sdr.start_receive()
        self.sdr.grab_samples(buf)
        self.sdr.stop_receive()
        return buf
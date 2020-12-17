import time
import radio
import numpy as np
import datetime

class Data:
    def __init__(self, freq, sr, tgt):
        self.freq = freq
        self.sr = sr
        self.sd = 1/sr
        self.tgt = tgt
        self.raw = None
        connect = 5
        while(connect):
            try:
                self.sdr = radio.Radio()
                break
            except:
                time.sleep(1)
                connect -= 1
        if connect == 0:
            raise RuntimeError('Failed to connect to SDR')
        self.sdr.set_sample_rate(self.sr)
        self.sdr.set_center_frequency(self.freq)
        #self.sdr.set_gain(40)

    def _data(self,snap):
        nsamps = snap/self.sd
        samps = np.array([],np.complex64)
        buf = np.array([0]*self.sdr.get_buffer_size(),np.complex64)
        self.sdr.start_receive()
        while(len(samps) < nsamps):
            try:
                self.sdr.grab_samples(buf)
            except:
                #print(e)
                continue
            samps = np.append(samps,buf)
        self.sdr.stop_receive()
        return samps

    def _to_file(self,data,fname):
        dt = datetime.datetime.now().strftime("%Y%m%d_%X")
        if fname == None:
            # TODO: where to save on default
            np.save('%s_%s.npy'%(self.tgt,dt),data)
        # TODO: save to different location

    def data_to_file(self,snap,fname=None):
        samps = self._data(snap)
        self._to_file(samps,fname)
        return samps
    
    def stream_to_file(self):
        self._to_file(self.raw)   

    def data_to_buf(self,q,snap,stop_flag):
        while(not stop_flag.is_set()):
            q.put(self._data(snap))
            time.sleep(5)
import numpy as np
import adsb_constants as adsb


class Signal:
    def __init__(self,sig):
        self.mean = self._mean(sig)
        self.median = self._median(sig)
        self.avg_pwr = self._avg_pwr(sig)
        self.mad = self._mad(sig)
        self.stdev_from_mad = self._stdev_from_mad(sig)
    
    def _mean(self,sig):
        return np.mean(sig)
    
    def _median(self, sig):
        return np.median(sig)

    def _avg_pwr(self, sig):
        if self.mean <= adsb.MEAN_THRESH and self.mean >= adsb.MEAN_THRESH*-1:
            return np.var(sig)
        else:
            return np.mean(np.abs(sig)**2)

    def _mad(self,sig):
        return np.median(np.abs(sig - self.median))

    def _stdev_from_mad(self,sig):
        return self.mad*adsb.K
        

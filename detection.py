import numpy as np
import signal_stats
#import adsb_constants

class Detection:
    def __init__(self, stream, trfact, mask, detThresh): 
        #self.mask = mask - .25
        self.mask = mask
        self.maskLen = len(mask)
        self.maskMean = np.sum(mask)/len(mask)
        self.stream = np.abs(stream)
        sig = signal_stats.Signal(self.stream)
        self.median = sig.median
        self.stddev = sig.stdev_from_mad
        self.trfact = trfact
        self.thresh = self.median + self.trfact*self.stddev
        self.detThresh = detThresh
    
    def detect(self):
        candidates = self._idx_above_stddev()
        return self._cross_correlation(candidates)

    def _idx_above_stddev(self):
        candidates = []
        for idx,sample in enumerate(self.stream):
            if sample > self.thresh and idx > self.maskLen/2:
                candidates.append(idx)
        return candidates

    def _cross_correlation(self, candidates):
        detIdx = {}
        #wIdx = (len(self.mask)/2*-1,len(self.mask)/2)
        for cIdx in candidates:
            cc = 0
            w = self.stream[cIdx : cIdx + self.maskLen]
            if len(w) < self.maskLen:
                continue
            wMean = np.mean(w)
            c = np.sqrt(abs((w-wMean).dot(w - wMean)))
            p = np.sqrt(abs((self.mask-self.maskMean).dot(self.mask - self.maskMean)))
            for j in range(self.maskLen):
                cc += (w[j] - wMean)*(self.mask[j]-self.maskMean)/(c*p)
            if cc > self.detThresh:
                # print('Found detect at idx: %d'%cIdx)
                # print('Detect score: %f'%cc)
                detIdx[cIdx] = cc
        return detIdx


                


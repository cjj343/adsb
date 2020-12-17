import numpy as np
import adsb_constants as adsb
import pyModeS as pms
import copy
import time

class Demod:

    def __init__(self, detects, results):
        self.detects = detects
        self.bits = np.zeros(shape=(len(self.detects),adsb.MSG_BITS),dtype=int)
        self.bytes = []
        self.planes = results

    def demod(self):
        self._demod()
        self._bit_to_byte()
        self._decode()

    def _demod(self):
        for dIdx,msg in enumerate(self.detects):
            for sIdx,samp in enumerate(msg[adsb.PREAM_LEN:-1:2]):
                # 2 samples per bit
                # If sample 1 is > than sample 2, then 1 - else 0
                if samp > msg[adsb.PREAM_LEN + sIdx * 2 + 1]:
                    self.bits[dIdx][sIdx] = 1

    def _bit_to_byte(self):
        for msg in self.bits:
            # Take the bits and turn into hexadecimal
            # Get rid of the leading '0x' for the decoder
            self.bytes.append(str(hex(int(''.join(map(str, msg)), 2))[2:]))
    
    def _decode(self):
        for msg in self.bytes:
            # Get downlink format first so we know how to process
            df = pms.adsb.df(msg)
            # Only worried about Mode-S Air to Ground (DF 17) messages for now
            if df == 17:
                # The ICAO address is unique - use as key
                icao = pms.adsb.icao(msg)
                if icao not in self.planes.keys():
                    self.planes[icao] = copy.deepcopy(self.planes['NULL'])
                # The type code tells us what information the packet contains
                tc = self.planes[icao]['typecode'] = pms.adsb.typecode(msg)
                if tc >=1 and tc <= 4:
                    self.planes[icao]['callsign'] = pms.adsb.callsign(msg)
                elif tc >= 5 and tc <= 8:
                    speed,angle,vertical_rate,speed_type = pms.adsb.velocity(msg)
                    self.planes[icao]['speed'] = speed
                    self.planes[icao]['angle'] = angle
                    self.planes[icao]['vertical_rate'] = vertical_rate
                    self.planes[icao]['speed_type'] = speed_type
                elif tc >= 9 and tc <= 18:
                    self.planes[icao]['altitude'] = pms.adsb.altitude(msg)
                    # Get the even/odd flag which tells us how to decode the position                            
                    isodd = pms.adsb.oe_flag(msg)
                    if isodd:
                        self.planes[icao]['odd'] = msg
                        self.planes[icao]['time1'] = time.time()
                    else:
                        self.planes[icao]['even'] = msg
                        self.planes[icao]['time0'] = time.time()                       
                    if self.planes[icao]['odd'] != '' and self.planes[icao]['even'] != '':
                        self.planes[icao]['position'] = pms.adsb.position(self.planes[icao]['even'],
                                                                          self.planes[icao]['odd'],
                                                                          self.planes[icao]['time0'],
                                                                          self.planes[icao]['time1'],
                                                                          36.6,121.89)
 
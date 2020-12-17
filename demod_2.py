import numpy as np
import adsb_constants as adsb
from pprint import pprint
import copy
import time

class Demod:

    def __init__(self, detects, results):
        self.detects = detects
        self.bits = np.zeros(shape=(len(self.detects),adsb.MSG_BITS),dtype=int)
        self.bytes = np.zeros(shape=(len(self.detects),adsb.MSG_BYTES),dtype=int)
        self.planes = results

    def demod(self):
        self._detect_to_bit()
        self._bit_to_byte()
        self._decode()

    def _detect_to_bit(self):
        for dIdx,msg in enumerate(self.detects):
            for sIdx,samp in enumerate(msg[adsb.PREAM_LEN:-1:2]):
                # 2 samples per bit
                # If sample 1 is > than sample 2, then 1 - else 0
                if samp > msg[adsb.PREAM_LEN + sIdx * 2 + 1]:
                    self.bits[dIdx][sIdx] = 1

    def _bit_to_byte(self):
        for mIdx,msg in enumerate(self.bits):
            for i in range(adsb.MSG_BYTES):
                self.bytes[mIdx][i] = int(('').join(str(x) for x in msg[i*8:i*8+8]), 2)
    
    def _message_mode(self, msgType):
        if ( msgType == 16 or msgType == 17 or msgType == 19 or msgType == 20 or msgType == 21):
            return adsb.MSG_BITS
        else:
            return adsb.SHORT_MSG_BITS

    def _crc(self,msg,bits,trimmed=False):
        for i in range(bits - len(adsb.GENERATOR)):
            if msg[i] == 1:
                for j in range(len(adsb.GENERATOR)):
                    msg[i + j] = msg[i+j] ^ adsb.GENERATOR[j]
        return msg[-1*len(adsb.GENERATOR):] # 24 bit crc remainder.
        
    def _decode(self):
        for msg,msgBits in zip(self.bytes,self.bits):
            # Bits 1-5 are the downlink format
            df = int(''.join(map(str, msgBits[0:5])), 2)
            # Bits 6-8 are the capability
            ca = int(''.join(map(str, msgBits[5:8])), 2)
            msgLen = self._message_mode(df)
            crc = self._crc(msgBits,msgLen)
            # All zeroes indicate a passing CRC
            if 1 not in crc:
                print(df,ca)
                # ICAO address ( airplane address )
                # Bytes 1-3 (0 index) contain unique ICAO in hex
                #aa1 = msg[1]
                #aa2 = msg[2]
                #aa3 = msg[3]
                addr = hex(int(''.join(map(str, msgBits[8:32])), 2))
                addr = addr.replace(' ','')
                if addr not in self.planes.keys():
                    self.planes[addr] = copy.deepcopy(self.planes['NULL'])
                # DF-17 - Mode-S packets that we can decode
                if df == 17:
                    # Get DF 17 (ADSB) extended squitter types
                    esMsgType = msg[4] >> 3 # extended squitter message type
                    esMsgSubType = msg[4] & 7 # extended squitter sub message type
                    # Data bits contain flight number
                    if esMsgType >=1 and esMsgType <= 4:
                        aircraft_type = esMsgType - 1
                        fnum = msg[5] << 40 | msg[6] << 32 | msg[7] << 24 | msg[8] << 16 | msg[9] << 8 | msg[10]
                        fnum = self._decode_addr(format(fnum,'048b'))
                        self.planes[addr]['planetype'] = aircraft_type
                        self.planes[addr]['flightnum'] = fnum
                    # Data bits contain lat/lon data
                    elif ( esMsgType >= 9 and esMsgType <= 18 ):                            
                        isodd = msg[6] & (1<<2)
                        lat_enc = ((msg[6] & 3) << 15) | (msg[7] << 7) | (msg[8] >> 1) 
                        lon_enc = ((msg[8] & 1) << 16) | (msg[9] << 8) | msg[10]
                        if isodd:
                            self.planes[addr]['lat1'] = lat_enc
                            self.planes[addr]['lon1'] = lon_enc
                            self.planes[addr]['time1'] = time.time()
                        else:
                            self.planes[addr]['lat0'] = lat_enc
                            self.planes[addr]['lon0'] = lon_enc
                            self.planes[addr]['time0'] = time.time()                       
                        if abs(self.planes[addr]['time0'] - self.planes[addr]['time1']) <= 10:
                            self._decode_CPR(self.planes[addr])
                    elif ( esMsgType == 19 and esMsgSubType >=1 and esMsgSubType <= 4 ):
                        if  ( esMsgSubType == 1 or esMsgSubType == 2):
                            ew_dir = (msg[5]&4) >> 2
                            ew_velocity = ((msg[5]&3) << 8) | msg[6]
                            ns_dir = (msg[7]&0x80) >> 7
                            ns_velocity = ((msg[7]&0x7f) << 3) | ((msg[8]&0xe0) >> 5)
                            vert_rate_source = (msg[8]&0x10) >> 4
                            vert_rate_sign = (msg[8]&0x8) >> 3
                            vert_rate = ((msg[8]&7) << 6) | ((msg[9]&0xfc) >> 2)
                            # Compute velocity and angle from the two speed  components. 
                            velocity = np.sqrt(ns_velocity*ns_velocity+ew_velocity*ew_velocity)
                            if (velocity):
                                ewv = ew_velocity
                                nsv = ns_velocity
                                if (ew_dir): ewv *= -1
                                if (ns_dir): nsv *= -1
                                heading = np.arctan2(ewv,nsv)
                                # We don't want negative values but a 0-360 scale. 
                                if (heading < 0):
                                    heading += 2 * np.pi
                            else:
                                heading = 0
                            self.planes[addr]['heading'] = heading
                        if esMsgSubType == 3 or esMsgSubType == 4:
                            self.planes[addr]['heading'] = (360 / 128) * (((msg[5] & 3) << 5) | (msg[6] >> 3)) * np.pi / 180

    def _decode_addr(self,bits):
        addrStr = ''
        for i in range(0,len(bits),6):
            addrStr += adsb.AIS_CHARS[int(bits[i:i+6],2)]
        return addrStr
            
    def _fix_errors( self, msg, bits, crc ):
            aux = copy.deepcopy(msg[:bits//8])
            for j in range(bits):
                byte = j//8
                bit = j%8
                bitmask = 1 << (7 - bit)
                aux[byte] ^= bitmask
                crc2 = self._checksum(aux,bits,True)
                crcok = (crc == crc2)
                if crcok:
                    for i in np.r_[:bits//8]:
                        msg[i] = aux[i]
                    break
                aux[byte] ^= bitmask
            return crcok
        
    def _NL(self, rlat):
        # A.1.7.2.d (page 9)
        NZ = 15
        return np.floor( 2 * np.pi / 
                        (np.arccos( 1 - (1 - np.cos( np.pi / (2 * NZ )) ) 
                                / np.cos( np.pi / 180 * abs(rlat) ) ** 2 )))

    def _cprN(self, lat, isodd):
        nl = self._NL(lat) - isodd
        if (nl < 1):
            nl = 1
        return nl

    def _Dlon(self, lat, isodd):
        return 360.0 / self._cprN(lat, isodd)
            
    def _cprmod(self, a, b):
        res = a % b
        if (res < 0):
            res = res + b
        return res

    def _decode_CPR(self, plane):
        AirDlat0 = 360.0 / 60
        AirDlat1 = 360.0 / 59
            
        lat0 = plane['lat0']
        lat1 = plane['lat1']
        lon0 = plane['lon0']
        lon1 = plane['lon1']
            
        j = np.floor(((59*lat0 - 60*lat1) / 131072) + 0.5)
            
        rlat0 = AirDlat0 * (self._cprmod(j,60) + lat0 / 131072)
        rlat1 = AirDlat1 * (self._cprmod(j,59) + lat1 / 131072)
            
        if (rlat0 >= 270):
            rlat0 = rlat0 - 360
                
        if (rlat1 >= 270):
            rlat1 = rlat1 - 360
                
        if (self._NL(rlat0) != self._NL(rlat1)):
            print('Warning')
            #return
            
        if (plane['time0'] > plane['time1']) :
            # Use even packet.
            ni = self._cprN(rlat0,0)
            m = np.floor((((lon0 * (self._NL(rlat0)-1)) -
                        (lon1 * self._NL(rlat0))) / 131072) + 0.5)
            lon = self._Dlon(rlat0,0) * (self._cprmod(m,ni)+lon0/131072)
            lat = rlat0
        else:
            # Use odd packet
            ni = self._cprN(rlat1,1)
            m = np.floor((((lon0 * (self._NL(rlat1)-1)) - 
                        (lon1 * self._NL(rlat1))) / 131072) + 0.5)
            lon = self._Dlon(rlat1,1) * (self._cprmod(m,ni)+lon1/131072)
            lat = rlat1
        if ( lon > 180 ):
            lon = lon - 360
        plane['position'] = (lat, lon)
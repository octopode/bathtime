#!/usr/bin/env python3

"""
neslabrte.py

driver module for controlling VWR/Polyscience circulator with
Advanced Programmable Controller
(should also work with Advanced Digital Controller per manual)
v0.5 (c) JRW 2023 - jwinnikoff@g.harvard.edu

GNU PUBLIC LICENSE DISCLAIMER:
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

#import __future__ # supposed to be 2/3 compatible
import serial # pip install pyserial
from warnings import warn

## binary encode/decode functions
    
class TCal:
    "Class for digital linear calibration"
    def __init__(self, slope, xcept):
        "Slope and intercept convert from reference to actual"
        self.__slope__ = slope
        self.__xcept__ = xcept
    reset = __init__ # alias
    def ref2act(self, temp_ref):
        return ((temp_ref * self.__slope__) + self.__xcept__)
    def act2ref(self, temp_act):
        return ((temp_act - self.__xcept__) / self.__slope__)

class PolysciController(TCal):
    "Class for a waterbath controller"
    def __init__(self, port, multidrop=False, addr=1, baud=9600, timeout=1, parity=serial.PARITY_NONE, rtscts=False):
        """
        Open serial interface~~, return fault status.~~
        The serial handle becomes a public instance object.
        """
        self.__ser__ = serial.Serial(port=port, baudrate=baud, timeout=timeout, parity=parity)
        self.__ser__.flush()
        self.__multidrop__ = multidrop
        self.__addr__ = addr
        # initialize calibrations at unity
        # these can be adjusted by bath.cal_ext.reset(slope, xcept)
        self.cal_int = TCal(1, 0)
        self.cal_ext = TCal(1, 0)
        # persistently enable command echo; other methods count on it
        self.echo(True, persist=True)
        
    def query(self, cmd, val=None, persist=False):
        "Send a query and return value, success, or failure"
        
        tries = 0
        while True: # persistence loop escaped by return
            tries += 1
            # send query
            if self.__multidrop__:
                query = '@' + str(self.__addr__).zfill(3)
            else:
                query = ''
            query += cmd
            if val is not None:
                query += str(val)
            #print(query) #TEST
            self.__ser__.write((query+'\r').encode())
            self.__ser__.flush()
            
            # read full response
            reply = self.__ser__.read_until(b'\r').decode().strip()
            
            # check to make sure the device understood (by echo)
            #20230104 short-circuiting the echo; it doesn't work!
            if (reply[-1] != '?') or (reply[:len(cmd)] == cmd) and (reply[-1] == '!'):
                # excise the return from the center
                #retval = reply[len(cmd):-1]
                retval = reply
                if len(retval):
                    # cast to float if possible
                    try: return float(retval)
                    except: return retval
                # (if any)
                else: return True
            else:
                if persist:
                    warn("Invalid echo: should be {}...{}, received {}. Attempt #{}".format(
                        cmd, '!',
                        reply,
                        tries
                    ))
                else: return False # and break out of loop
        
    def disconnect(self):
        "Close serial interface."
        self.__ser__.reset_input_buffer()
        self.__ser__.reset_output_buffer()
        self.__ser__.close()
        
    ## serial call-response shorthand
    #call_code = {
    #    "on"      : 'SO',
    #    "temp_set"   : 'SS',
    #    "temp_get_int"   : 'V',
    #    "mcu_temp"  : 'T',
    #    "zero"      : 'Z',
    #    "get_od600" : 'O',
    #    "get_qval"  : 'Q',
    #    "get_reflux": 'R',
    #    "get_xmslux": 'X'
    #}
    #
    ## declare getters programatically
    #for func, lett in call_resp.items():
    #    exec("def {}(self): return self.quereply('{}')".format(func, lett))
    
    # register setters/getters
    ## these are for static values that are changeable only by user command
    ## i.e. not dynamic measured values
    
    ### utility commands
    ### could write dict-producing omnibus funcs to make backward-compatible with neslabrte
    
    def echo(self, status, **kwargs):
        "Enable or disable command echo. NOTE: command echo does not appear to work!"
        return self.query("SE", val=int(status), **kwargs)
        
    def auto_restart(self, status, **kwargs):
        "Enable or disable auto-restart on power failure."
        return self.query("SW", val=int(status), **kwargs)
        
    def pump_speed(self, spd=None, **kwargs):
        "Get or set on-status of the circulator."
        # get
        if spd is None: return bool(self.query("RM", **kwargs))
        # set
        else: 
            # take an input float of 0-1 and convert to 0-100,
            # rounded to nearest 5
            if spd > 1: spd = 1
            elif spd < 0: spd = 0
            else: spd = 100*round(20*spd)/20
            return self.query("SM", val=int(spd), **kwargs)
            
    def autocool(self, temp=None, **kwargs):
        "Get or set(?) autocool setpoint. Analogous to fullrange_cool."
        # get
        if temp is None: return self.query("RA", **kwargs)
        # set - not documented but works
        else: return self.query("SA", val=temp, **kwargs)
            
    def faults(self, status, **kwargs):
        "Check fault status."
        return bool(self.query("RF", **kwargs))
        
    ### standard commands
            
    def on(self, status=None, **kwargs):
        "Get or set on-status of the circulator."
        # get
        if status is None: return bool(self.query("RO", **kwargs))
        # set
        else: return self.query("SO", val=int(status), **kwargs)
            
    def probe_ext(self, status, **kwargs):
        "Set status of external probe (used for control, or not?)"
        return self.query("SJ", val=int(status), **kwargs)
        
    def temp_set(self, temp=None, **kwargs):
        "Set or get temperature setpoint."
        # get
        if temp is None: return self.query("RS", **kwargs)
        # set - need any zero padding?
        else: return self.query("SS", val=temp, **kwargs)
            
    def fault_lo(self, limit=None, **kwargs):
        "Set or get low-temp ALARM. The fault limit must be set at front panel!"
        # get
        if limit is None: return self.query("RL", **kwargs)
        # set - need any zero padding?
        else: return self.query("SL", val=str(round(limit)).zfill(3), **kwargs)
            
    def fault_hi(self, limit=None, **kwargs):
        "Set or get low-temp ALARM. The fault limit must be set at front panel!"
        # get
        if limit is None: return self.query("RH", **kwargs)
        # set - need any zero padding?
        else: return self.query("SH", val=str(round(limit)).zfill(3), **kwargs)
            
    # method aliases for back-compat w/Thermo Isotemp
    warn_lo = fault_lo
    warn_hi = fault_hi
            
    # There does not appear to be support for PID tuning via serial
    # May implement a topside PID subclass later
    #def pid(self, drive, p=None, i=None, d=None):
    #    """
    #    Get or set PID bandwidths for heater or chiller drive (H/C).
    #    p in %           (0.1-99.9)
    #    i in repeats/min (0-9.99)
    #    d in min         (0-5.0)
    #    """
    #    # bit shift register for heat/cool drive
    #    drive_shift = {'H': 0, 'C': 3}
    #    # get proportional band
    #    if p is None: p = threebyte2float(self.query([0x71+drive_shift]))
    #    # set proportional band
    #    else: p = (threebyte2float(self.query([0xF1+drive_shift], dat=int2int16(p*10))) == p)
    #    # get integral band
    #    if i is None: i = threebyte2float(self.query([0x72+drive_shift]))
    #    # set integral band
    #    else: i = (threebyte2float(self.query([0xF2+drive_shift], dat=int2int16(i*100))) == i)
    #    # get derivative band
    #    if d is None: d = threebyte2float(self.query([0x73+drive_shift]))
    #    # set derivative band
    #    else: d = (threebyte2float(self.query([0xF3+drive_shift], dat=int2int16(d*10))) == d)
    #    return((p, i, d))
                    
    def units(self, unit=None, **kwargs):
        "Get or set(?) temperature unit (C/F)."
        # get
        if unit is None: return bool(self.query("RU", **kwargs))
        # set - Not documented but works
        else: return self.query("SU", val=unit, **kwargs)
    
    # data requests
    ## for data measured in real time
            
    def temp_get_int(self, **kwargs):
        "Get current temp at internal sensor."
        return self.query("RT", **kwargs)
        
    def temp_get_ext(self, **kwargs):
        "Get current temp at external sensor."
        return self.query("RR", **kwargs)
            
    def temp_get_act(self, ext=None, **kwargs):
        "Get calibrated temp, by default from active sensor."
        # if sensor not specified, use the active one
        if ext is None: ext = self.probe_ext()
        if not ext: return(cal_int.ref2act(self.temp_get_int(**kwargs)))
        else: return(cal_ext.ref2act(self.temp_get_ext(**kwargs)))
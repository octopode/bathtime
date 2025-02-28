#!/usr/bin/python3

"""
Follow a supplied temperature program,
logging process and reference temps all the way
"""

from __future__ import print_function

import sys
import argparse
import traceback
import time
import numpy as np
import pandas as pd
import vwrpolysci as vwr

class QTIProbe:
    "Class for QTI 6001 USB temperature probe"
    def __init__(self, port, baud=9600, timeout=1):
        """
        Open serial interface, return fault status.
        The serial handle becomes a public instance object.
        """
        import serial
        self.__ser__ = serial.Serial(port=port, baudrate=baud, timeout=timeout)
        self.__ser__.flush()
        # initialize
        self.__ser__.write(b'0')
        self.__ser__.flush()
        
    def temp_get(self):
        "Return current temperature."
        self.__ser__.write(b'2')
        self.__ser__.flush()
        return float(self.__ser__.readline().decode().strip())
        
def parse_args(argv):
    "Parse command line arguments."
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)
    #if not len(argv): argv.append("-h")
    parser.add_argument('-p', "--port", help="serial port for the bath")
    parser.add_argument('-o', "--outfile", help="data log file")
    # return as a dict
    return vars(parser.parse_args(argv))

def main(args, stdin, stdout, stderr):
    "Run through temperature program, logging data in real time along the way."
    if not stdin.isatty():
        # if a state table is passed on stdin, read it
        print("reading states from stdin", file=stderr)
        states = pd.read_csv(stdin, sep='\t')
    else:
        print("ERR: you need to pass the state table on stdin!", file=stderr)
        exit(1)
    
    # open output file
    with open(args["outfile"], 'a+', buffering=1) as hand_log:
    
        # write header
        # important that all vars collected below are accounted for here!
        header = sorted([
            "clock", 
            "watch", 
            "temp_int", 
            "temp_ext", 
            #"temp_ref", 
            # command vars are automatically inserted
        ] + list(states.head()))
        hand_log.write('\t'.join(header) + '\n')
        
        # init water bath
        bath = vwr.PolysciController(port=args["port"])
        #nist = QTIProbe(port="/dev/cu.usbmodem141201") # using an Arduino today
        
        # do some initialization to ensure devices are similarly set
        print("initializing...", end='', file=stderr)
        bath.fault_lo( -5, persist=True)
        bath.fault_hi(120, persist=True)
        bath.autocool(45, persist=True)
        bath.pump_speed(0.7, persist=True)
        print("√", file=stderr)
            
        ## run experiment
        
        # start experiment timer (i.e. stopwatch)
        time_start = time.time()
        
        # start circulator
        while not bath.on(): bath.on(1) # persistence problems
        
        # switch to internal probe
        bath.probe_ext(0, persist=True)
        
        # iterate over test states
        for state_num in range(states.shape[0]):
        
            # make dicts for this state, the last, and the next
            state_curr = states.iloc[state_num+0].to_dict()
            
            time_state = time.time()
            
            # set bath temperature persistently
            bath.temp_set(state_curr["temp_set"], persist=True)
            print("temp set to {} deg C".format(state_curr["temp_set"]), file=stderr)
            
            # log data for the prescribed period
            while time.time() - time_state < state_curr["time"]:
                while True: # persistent polling
                    try:
                        data = {
                            "clock": time.strftime("%Y%m%d %H%M%S"), 
                            "watch": time.time() - time_start, 
                            "temp_int": bath.temp_get_int(),
                            "temp_ext": bath.temp_get_ext(),
                            #"temp_ref": nist.temp_get(), # has 1 s latency but who cares
                        }
                        break
                    except: print(traceback.format_exc())
                data.update(state_curr) # add the command vars to the log
                hand_log.write('\t'.join([str(data[key]) for key in sorted(data.keys())]) + '\n')
                print("waiting {}/{} s".format(round(time.time()-time_state), data["time"]), file=stderr, end='\r')
            
            print('', file=stderr)
            
        # shut down hardware
        bath.on(0)
        
if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args, sys.stdin, sys.stdout, sys.stderr)
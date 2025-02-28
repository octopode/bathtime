#!/usr/bin/python3

"""
Follow a supplied temperature program,
logging process and reference temps all the way
"""
## ATTENTION: this script is set up for Windows

# the serial port to which the NESLAB waterbath is connected
bathport = "COM11"

from __future__ import print_function

from os import getcwd
import sys
import traceback
import time
import numpy as np
import pandas as pd
import neslabrte

delay = 0.1 # approximate (overestimate) of sampling period in seconds

# start a timestamped datalog file
file_log = getcwd() + r"\thermolog_" + time.strftime("%Y%m%dT%H%M") + ".tsv"
        
if not sys.stdin.isatty():
    # if a state table is passed on sys.stdin, read it
    print("reading states from sys.stdin", file=sys.stderr)
    states = pd.read_csv(sys.stdin, sep='\t')
else:
    print("ERR: you need to pass the state table on sys.stdin!", file=sys.stderr)
    exit(1)

# open output file
with open(file_log, 'a+', buffering=1) as hand_log:

    # write header
    header = sorted(["clock", "watch", "temp_int", "temp_ext"] + list(states.head()))
    hand_log.write('\t'.join(header) + '\n')
    
    # init water bath
    bath = neslabrte.NeslabController(port=bathport)

    ## run experiment
    
    # start experiment timer (i.e. stopwatch)
    time_start = time.time()
    
    # start circulator
    #while not bath.on(): bath.on(1) # persistence problems
    bath.on(1)
    
    # switch to external probe
    #while bath.probe_ext(): bath.probe_ext(1)
    
    # iterate over test states
    for state_num in range(states.shape[0]):
    
        # make dicts for this state, the last, and the next
        state_curr = states.iloc[state_num+0].to_dict()
        print(state_curr) #TEST
        
        time_state = time.time()
        
        # set bath temperature persistently
        while not bath.temp_set(state_curr["temp_set"]): pass
        print("temp set to {} deg C".format(state_curr["temp_set"]), file=sys.stderr)
        
        # log data for the prescribed period
        while time.time() - time_state < state_curr["time"]:
            while True: # persistent polling
                try:
                    data = {
                        "clock": time.strftime("%Y%m%d %H%M%S"), 
                        "watch": time.time() - time_start, 
                        "temp_int": bath.temp_get_int(),
                        "temp_ext": bath.temp_get_ext(),
                    }
                    break
                #except: pass
                except: print(traceback.format_exc())
            time.sleep(delay)
            data.update(state_curr) # add the command vars to the log
            hand_log.write('\t'.join([str(data[key]) for key in sorted(data.keys())]) + '\n')
            print("waiting {}/{} s".format(round(time.time()-time_state), data["time"]), file=sys.stderr, end='\r')
        
        print('', file=sys.stderr)
        
    # shut down hardware
    #bath.on(0)
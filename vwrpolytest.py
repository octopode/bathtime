#!/usr/bin/env python3

"""
initialize Neslab water bath, then provide user with an interactive console for debugging
"""

import vwrpolysci as vwr
import traceback
import __future__
import sys

bath = vwr.PolysciController(port=sys.stdin.read().strip())

while True:
    # reset stdin
	sys.stdin = open('/dev/tty', 'r')
	cmd = input("bath.")
	try:
	    print(eval("bath.{}".format(cmd)))
	except:
		traceback.print_exc()
		bath.disconnect()
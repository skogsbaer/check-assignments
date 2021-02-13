import sys
import traceback

def warn(msg):
    print('WARN: ' + msg)

VERBOSE = False

def enableVerboseLogging():
    global VERBOSE
    VERBOSE = True

def verbose(msg):
    if VERBOSE:
        print('[V] ' + msg)

def abort(msg):
    print('ERROR: ' + msg)
    traceback.print_stack(file=sys.stdout)
    sys.exit(1)

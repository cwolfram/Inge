#!/usr/bin/env python


import sys
import shelve
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

from xml.etree import ElementTree


DBPATH = "lib/macmodelshelf"

try:
    macmodelshelf = shelve.open(DBPATH)
except BaseException as e:
    print ("Couldn't open macmodelshelf.db: %s" % e, file=sys.stderr)
    sys.exit(1)


def model_code(serial):
    if "serial" in serial.lower(): # Workaround for machines with dummy serial numbers.
        return None
    if len(serial) in (12, 13) and serial.startswith("S"): # Remove S prefix from scanned codes.
        serial = serial[1:]
    if len(serial) in (11, 12):
        return serial[8:]
    return None
    

def lookup_mac_model_code_from_apple(model_code):
    try:
        f = urlopen("http://support-sp.apple.com/sp/product?cc=%s&lang=en_US" % model_code, timeout=2)
        et = ElementTree.parse(f)
        return et.findtext("configCode")
    except:
        return None
    

def model(code):
    global macmodelshelf
    code = code.upper()
    try:
        model = macmodelshelf[code]
    except KeyError:
        print ("Looking up %s from Apple" % code, file=sys.stderr)
        model = lookup_mac_model_code_from_apple(code)
        if model:
            macmodelshelf[code] = model
    return model


def _dump():
    print ("macmodelshelfdump = {")
    for code, model in sorted(macmodelshelf.items()):
        print ('    "%s": "%s",' % (code, model))
    print ("}")
    

if __name__ == '__main__':
    try:
        if sys.argv[1] == "dump":
            _dump()
            sys.exit(0)
        if len(sys.argv[1]) in (11, 12, 13):
            m = model(model_code(sys.argv[1]))
        else:
            m = model(sys.argv[1])
        if m:
            print (m)
            sys.exit(0)
        else:
            print ("Unknown model %s" % repr(sys.argv[1]), file=sys.stderr)
            sys.exit(1)
    except IndexError:
        print ("Usage: macmodelshelf.py serial_number")
        sys.exit(1)

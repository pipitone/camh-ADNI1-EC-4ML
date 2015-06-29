#!/usr/bin/env python
# vim: sw=4 ts=4 expandtab:
"""
Reads a dataset, and looks up DX by image ID

Usage: 
    add-classes.py [options] <dataset.h5>

Options:
    --progress-freq N     Show progress every N images processed [default: 10000]
    --dx-table FILE       CSV mapping ImageID to Diagnosis [default: ADNI1_1.5T_with_scaled_2.csv]
"""

from time import time
import datetime
import glob
import itertools
import math
import matplotlib
import numpy as np
import tables as tb
import os.path
import random
import sys
import re
from docopt import docopt

def progress(complete,total,duration,period):
    print "Completed {}/{}. Last {} in {:.0f}s. Estimated time left: {:.0f}m".format(
            complete,total,period,duration,(duration/period)*(total-complete)/60)

if __name__ == '__main__':

    arguments = docopt(__doc__) 
    datafile  = arguments['<dataset.h5>']
    printfreq = int(arguments['--progress-freq'])

    # get data
    FILTERS = tb.Filters(complevel=5,complib='zlib')
    datah = tb.open_file(datafile, mode='a', filters=FILTERS)
    files = datah.root.files

    # subject info by image ID
    import csv
    reader = csv.DictReader(open('ADNI1_1.5T_with_scaled_2.csv'),delimiter=';')
    dx_codes = { 'AD':  0, 'CN':  1, 'LMCI': 2  }
    dx = { d['Image_ID'] : dx_codes[d['DX.bl']] for d in reader }

    # extract a list of IDs from left/right dataset files
    # ID is just _I<number> in the file name
    ids = map(lambda x: re.search(r"_I(\d+)", x).group(1), files)

    classes = map(lambda x: dx[x], ids)
    if "classes" not in datah.root: 
        _ = datah.create_array(datah.root,'classes' ,classes)
    if "ids" not in datah.root: 
        _ = datah.create_array(datah.root,'ids' ,ids)
    datah.close() 

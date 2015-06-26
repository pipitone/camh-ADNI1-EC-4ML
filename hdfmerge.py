#!/usr/bin/env python
# vim: sw=4 ts=4 expandtab:
"""
Reads a bunch of label files and stores in HDF5 format. 

Usage: 
    hd5ify.py [options] <h5dir> <hfile.h5>

Options:
    --mask MASK           Mask for 1st stage filtering [default: mask.mnc]
    --maskpad N           Padding [default: 5]
"""
import sys
from docopt import docopt

def progress(complete,total,duration,period):
    print "Completed {}/{}. Last {} in {:.0f}s. Estimated time left: {:.0f}m".format(
            complete,total,period,duration,(duration/period)*(total-complete)/60)

if __name__ == '__main__':

    arguments = docopt(__doc__) 
    maskfile = arguments['--mask']
    maskpad  = int(arguments['--maskpad'])
    imagedir = arguments['<h5dir>']
    datafile = arguments['<hfile.h5>']

    print "Loading libraries..."
    from pyminc.volumes.factory import *
    from time import time
    import glob
    import numpy as np
    import numpy.ma as ma
    import tables as tb
    import os.path

    ###########################################################################
    # Build data array
    # 
    # Read all data files, but only voxels in data mask. 
    FILTERS = tb.Filters(complevel=5,complib='zlib')
    if os.path.exists(datafile):
        print "{} exists. ".format(datafile)
        sys.exit(1)

    fileh = tb.open_file(datafile, mode='w', title="data", filters=FILTERS)

    subfiles  = glob.glob(imagedir + '/*.h5')

    filelist = []
    for subfile in subfiles: 
        subfileh = tb.open_file(subfile, mode='r', title="data", filters=FILTERS)

        print "Loading data from {}".format(subfile)
        if not 'mask' in fileh.root:
            mask = subfileh.root.mask[:]
            _ = fileh.create_array(fileh.root,'mask',mask)
            dataarray = fileh.createEArray(fileh.root,'data',tb.BoolAtom(), 
                    shape=[0]+list(mask.shape))

        if not 'cropbbox_min' in fileh.root:
            _ = fileh.create_array(fileh.root,'cropbbox_min', 
                    subfileh.root.cropbbox_min[:]) 
        if not 'cropbbox_max' in fileh.root:
            _ = fileh.create_array(fileh.root,'cropbbox_max', 
                    subfileh.root.cropbbox_max[:]) 

        dataarray.append(subfileh.root.data[:])
        filelist.extend(subfileh.root.files)
        subfileh.close()

    _ = fileh.create_array(fileh.root, 'files', filelist)

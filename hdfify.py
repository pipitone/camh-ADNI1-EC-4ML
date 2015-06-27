#!/usr/bin/env python
# vim: sw=4 ts=4 expandtab:
"""
Reads a bunch of label files and stores in HDF5 format. 

Usage: 
    hd5ify.py [options] <mask> <labelval> <imagedir> <hfile.h5>

Arguments: 
    <mask>                Mask for 1st stage filtering
    <labelval>            Label to select from the mask when computing bounding box
    <imagedir>            Folder full of minc label files
    <hfile.h5>            Output file. 

Options:
    --maskpad N           Number of voxels to pad around the mask bbox [default: 5]
    --progress-freq N     Show progress every N images processed [default: 500]
"""

from docopt import docopt

def progress(complete,total,duration,period):
    print "Completed {}/{}. Last {} in {:.0f}s. Estimated time left: {:.0f}m".format(
            complete,total,period,duration,(duration/period)*(total-complete)/60)

if __name__ == '__main__':

    arguments = docopt(__doc__) 
    maskfile = arguments['<mask>']
    labelval = int(arguments['<labelval>'])
    imagedir = arguments['<imagedir>']
    datafile = arguments['<hfile.h5>']
    maskpad  = int(arguments['--maskpad'])
    printfreq         = int(arguments['--progress-freq'])

    print "Loading libraries..."
    from pyminc.volumes.factory import *
    from time import time
    import glob
    import numpy as np
    import numpy.ma as ma
    import tables as tb
    import os.path

    print "Creating list of images..."
    labelfiles = glob.glob(imagedir + '/*.mnc')

    print "{} images found.".format(len(labelfiles))
    print 

    ###########################################################################
    # Load mask and compute a bounding box
    # 
    # We need to mask when, because of memory limits, we can't read in a full
    # volume from each label. So here we just compute the bounding box of the
    # max, and use that to extract subvolumes from each label.

    # Get bounding box from average
    fullmask = volumeFromFile(maskfile).data

    # compute bounding box
    maskidx = np.argwhere(np.logical_and(fullmask > labelval - .5, fullmask < labelval + .5))
    minidx = maskidx.min(0) - maskpad
    maxidx = maskidx.max(0) + maskpad 
    mask = fullmask[minidx[0]:maxidx[0],minidx[1]:maxidx[1],minidx[2]:maxidx[2]]

    # indices to extract at first
    print "Mask bounding box: ", minidx, maxidx
    print

    ###########################################################################
    # Build data array
    # 
    # Read all data files, but only voxels in data mask. 
    FILTERS = tb.Filters(complevel=5,complib='zlib')
    if os.path.exists(datafile):
        fileh = tb.open_file(datafile, mode='a', title="data", filters=FILTERS)
    else: 
        fileh = tb.open_file(datafile, mode='w', title="data", filters=FILTERS)

    if not 'files' in fileh.root:
        _ = fileh.create_array(fileh.root,'files',labelfiles)
    if not 'mask' in fileh.root:
        _ = fileh.create_array(fileh.root,'mask',mask)
    if not 'cropbbox_min' in fileh.root:
        _ = fileh.create_array(fileh.root,'cropbbox_min', minidx) 
    if not 'cropbbox_max' in fileh.root:
        _ = fileh.create_array(fileh.root,'cropbbox_max', maxidx) 
    if not 'data' in fileh.root:
        print "Loading data into {}".format(datafile)
        dataarray = fileh.createEArray(fileh.root,'data',tb.BoolAtom(), 
                shape=[0]+list(mask.shape))

        t0 = time()
        for i, labelfile in enumerate(labelfiles):
            if i>0 and i % printfreq == 0: 
                progress(i,len(labelfiles),time()-t0,printfreq)
                t0 = time()

            data = volumeFromFile(labelfile).data[
                minidx[0]:maxidx[0],
                minidx[1]:maxidx[1],
                minidx[2]:maxidx[2]] == labelval
            data = np.logical_and(data > labelval - .5, data < labelval + .5)
            dataarray.append(data[np.newaxis,:])

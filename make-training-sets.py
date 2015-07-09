#!/usr/bin/env python
# vim: sw=4 ts=4 expandtab:
"""
Reads dataset and divides it into train/test/valid datasets. 

Usage: 
    make-training-sets.py [options] <input.h5> <output.h5>

Options:
    --progress-freq N     Show progress every N images processed [default: 10000]
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
    inputfile = arguments['<input.h5>']
    datafile  = arguments['<output.h5>']
    printfreq = int(arguments['--progress-freq'])
    dx_codes  = { 'AD':  0, 'CN':  1, 'LMCI': 2  }

    # get data
    FILTERS = tb.Filters(complevel=5,complib='zlib')
    inputh = tb.open_file(inputfile, mode='r', filters=FILTERS)
    files   = inputh.root.files.read()
    ids     = inputh.root.ids.read()
    classes = inputh.root.classes.read()

    classmap = { i:c for i,c in zip(ids, classes) } 

    #############################################################################
    # Make training, test, and validation datasets
    #
    AD_IDs = [ i for i,c in classmap.iteritems() if c == dx_codes['AD'] ]
    MC_IDs = [ i for i,c in classmap.iteritems() if c == dx_codes['LMCI'] ]
    CN_IDs = [ i for i,c in classmap.iteritems() if c == dx_codes['CN'] ]

    assert len(AD_IDs + CN_IDs + MC_IDs) == len(classmap.keys()), \
            len(AD_IDs + CN_IDs + MC_IDs)

    print "Number of subjects before matching: AD={}, MCI={}, CN={}".format(len(AD_IDs), len(MC_IDs), len(CN_IDs))

    # we need equal number of subjects in each group
    mingroupsize = min([len(AD_IDs), len(MC_IDs), len(CN_IDs)])
    AD_IDs = AD_IDs[:mingroupsize]
    MC_IDs = MC_IDs[:mingroupsize]
    CN_IDs = CN_IDs[:mingroupsize]

    print "Number of subjects after matching: AD={}, MCI={}, CN={}".format(len(AD_IDs), len(MC_IDs), len(CN_IDs))

    # shuffle each group
    random.shuffle(AD_IDs)
    random.shuffle(MC_IDs)
    random.shuffle(CN_IDs)

    # Divide the data into 7 groups. We'll put five groups in to training, 1 in validation, and 1 in test
    import random
    AD_n = len(AD_IDs)/7
    MC_n = len(MC_IDs)/7
    CN_n = len(CN_IDs)/7

    # make training, validation and test sets
    train_IDs = set(AD_IDs[:AD_n*5]       + MC_IDs[:MC_n*5]       + CN_IDs[:CN_n*5])
    valid_IDs = set(AD_IDs[AD_n*5:AD_n*6] + MC_IDs[MC_n*5:MC_n*6] + CN_IDs[CN_n*5:CN_n*6])
    test_IDs  = set(AD_IDs[AD_n*6:]       + MC_IDs[MC_n*6:]       + CN_IDs[CN_n*6:])

    assert len(train_IDs)+len(valid_IDs)+len(test_IDs) == mingroupsize*3, \
        len(train_IDs)+len(valid_IDs)+len(test_IDs)

    data = inputh.root.data

    def copy_data(targeth,name,source,idx):
        a = targeth.createCArray(targeth.root,name,tb.Int8Atom(), 
                shape=[len(idx)] + list(source.shape[1:]))
        print "Copying {} images to {}".format(len(idx),name)
        t0 = time()
        for i,ind in enumerate(idx):
            if i>0 and i % printfreq == 0: 
                progress(i,len(idx),time()-t0,printfreq)
                t0 = time()
            a[i,:] = source[ind,:]

    datah = tb.open_file(datafile, mode='w', title="data", filters=FILTERS)

    # compute indexes into datasets for train/validation/test
    # these aren't boolean mask indices, these are positions
    train_idx = [i for i,id_ in enumerate(ids) if id_ in train_IDs]
    valid_idx = [i for i,id_ in enumerate(ids) if id_ in valid_IDs]
    test_idx  = [i for i,id_ in enumerate(ids) if id_ in test_IDs]
    
    # shuffle those so the candidate labels for a subject don't appear together
    random.shuffle(train_idx)
    random.shuffle(valid_idx)
    random.shuffle(test_idx)

    print "Training set size:",len(train_idx)
    print "Validation set size:",len(valid_idx)
    print "Test set size:",len(test_idx)
    print "Dimensionality:",data.shape[1]
    print

    copy_data(datah,'train_data',data,train_idx)
    copy_data(datah,'test_data' ,data,test_idx)
    copy_data(datah,'valid_data',data,valid_idx)

    # compute corresponding DX classes and list of files
    train_classes = [classes[i] for i in train_idx]
    valid_classes = [classes[i] for i in valid_idx]
    test_classes  = [classes[i] for i in test_idx ]

    train_files   = [files[i] for i in train_idx]
    valid_files   = [files[i] for i in valid_idx]
    test_files    = [files[i] for i in test_idx ]
                                                             
    # save classes
    _ = datah.create_array(datah.root,'train_classes',np.array(train_classes,dtype='int8'))
    _ = datah.create_array(datah.root,'test_classes', np.array(test_classes,dtype='int8'))
    _ = datah.create_array(datah.root,'valid_classes',np.array(valid_classes,dtype='int8'))

    # save list of files
    _ = datah.create_array(datah.root,'train_files',train_files)
    _ = datah.create_array(datah.root,'test_files' ,test_files )
    _ = datah.create_array(datah.root,'valid_files',valid_files)

    # save data masks
    _ = datah.create_array(datah.root,'volmask'     ,inputh.root.volmask.read())
    _ = datah.create_array(datah.root,'datamask'    ,inputh.root.datamask.read())
    _ = datah.create_array(datah.root,'cropbbox_min',inputh.root.cropbbox_min.read()) 
    _ = datah.create_array(datah.root,'cropbbox_max',inputh.root.cropbbox_max.read()) 

    datah.close()
    inputh.close()

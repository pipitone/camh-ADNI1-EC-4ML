#!/usr/bin/env python
# vim: sw=4 ts=4 expandtab:
"""
Reads a bunch of label data, and removes outliers. Stores the results in HDF5

Outlier labels are: 
    - those that differ significantly from the mask 
    - those that have rarely appearing voxels

Usage: 
    remove-outliers-whole.py [options] <rawdata.h5> <output.h5>

Options:
    --freq-threshold N    If a voxel appears N% or fewer times in all of the
                          labels then images with this voxel set will be
                          considered outliers. [default: 1.0]
    --score-threshold N   Number of stddev's above average score (difference
                          against mask) which to exclude labels [default: 1.0]
    --progress-freq N     Show progress every N images processed [default: 10000]
"""

from docopt import docopt

def progress(complete,total,duration,period):
    print "Completed {}/{}. Last {} in {:.0f}s. Estimated time left: {:.0f}m".format(
            complete,total,period,duration,(duration/period)*(total-complete)/60)

if __name__ == '__main__':

    arguments = docopt(__doc__) 
    rawdatafile = arguments['<rawdata.h5>']
    datafile    = arguments['<output.h5>']
    printfreq   = int(arguments['--progress-freq'])
    freq_thresh_perc = float(arguments['--freq-threshold'])
    score_thresh = float(arguments['--score-threshold'])

    scoresfile        = datafile + '.scores_cache.npy'
    voxelfreqfile     = datafile + '.voxelfreq_{}thresh_cache.npy'.format(freq_thresh_perc)
    
    print "Loading libraries..."
    from time import time
    import glob
    import numpy as np
    import numpy.ma as ma
    import tables as tb
    import os.path

    FILTERS = tb.Filters(complevel=5,complib='zlib')
    rawfileh = tb.open_file(rawdatafile, mode='r', title="data", filters=FILTERS)
    rawdata  = rawfileh.root.data

    labelfiles = rawfileh.root.files
    mask = rawfileh.root.mask

    print "Images loaded: ", len(labelfiles)
    print 

    #############################################################################
    # Compute scores
    # 
    # Do a pass over the data files, and compute the "score" (number of label
    # voxels different from the average mask)

    if not os.path.exists(scoresfile):
        print "Computing mask difference scores..."
        scores = np.zeros(shape=(len(labelfiles)))  

        t0 = time()
        for i, labelfile in enumerate(labelfiles):
            if i>0 and i % printfreq == 0: 
                progress(i,len(labelfiles),time()-t0,printfreq)
                t0 = time()
        
            scores[i] = np.sum(np.abs(rawdata[i,:] - mask),axis=None)
    #     np.save(scoresfile,scores)
    else:
        print "Reading cached scores from {}".format(scoresfile)
        scores = np.load(scoresfile)

    assert rawdata.shape[0] == scores.shape[0]

    # exclude labels with scores differing too much from the mean
    passing_idx = scores < (np.average(scores)+score_thresh*np.std(scores))

    ###########################################################################
    # Compute outlier voxels
    # 
    # Outlier voxels are those voxels rarely appearing in most labels.
    # 
    # To compute do this we do a second pass over the data (excluding the
    # images with high scores computed above) and keep a running count per
    # voxel. 
    if not os.path.exists(voxelfreqfile):
        print "Computing outlier voxels..."
        voxel_freq_idx = np.zeros( shape=rawdata.shape[1:] )

        t0 = time()
        for i, labelfile in enumerate(labelfiles):
            if i>0 and i % printfreq == 0: 
                progress(i,len(labelfiles),time()-t0,printfreq)
                t0 = time()

            if not passing_idx[i]: continue

            data = rawdata[i,:]
            
            voxel_freq_idx = voxel_freq_idx + data

        #np.save(voxelfreqfile,voxel_freq_idx)
    else:
        print "Reading voxel frequencies from {}".format(voxelfreqfile)
        voxel_freq_idx = np.load(voxelfreqfile)

    freq_thresh  = (freq_thresh_perc/100.0)*rawdata.shape[0]
    outlier_mask = np.logical_or(voxel_freq_idx <= freq_thresh, 
                                voxel_freq_idx > (np.sum(passing_idx) - freq_thresh) )
   # outlier_mask = voxel_freq_idx <= freq_thresh
    data_mask    = voxel_freq_idx >  freq_thresh

    print "# samples = {}".format(rawdata.shape[0])
    print "# labels with passing scores (< {} stddev above mean): {}".format(score_thresh,np.sum(passing_idx))
    print "Outlier voxel frequency threshold: {}%".format(freq_thresh_perc)
    print "Outlier voxel frequency threshold #: {}".format(freq_thresh)
    print "Total # voxels in volume: ", np.prod(rawdata.shape[1:])
    print "# zero voxels:", len(np.where(voxel_freq_idx == 0)[0])
    print "# outlier voxels:", len(np.where(outlier_mask)[0])
    print "# data voxels:", len(np.where(data_mask)[0])
    print 

    ###########################################################################
    # Build data array
    # 
    # Ignore all high-scoring labels and labels with outlier voxels
    #
    # Read all data files, but only voxels in data mask. 
    flat_data_mask = data_mask.reshape(-1)

    if not os.path.exists(datafile):
        print "Loading data into {}".format(datafile)
        fileh = tb.open_file(datafile, mode='w', title="data", filters=FILTERS)
        dataarray = fileh.createEArray(fileh.root,'data',tb.BoolAtom(), 
                        shape=(0,np.sum(flat_data_mask)))

        images_used = []
        t0 = time()
        for i, labelfile in enumerate(labelfiles):
            if i>0 and i % printfreq == 0: 
                progress(i,len(labelfiles),time()-t0,printfreq)
                t0 = time()

            if not passing_idx[i]: continue

            data = rawdata[i,:]

            #outlier_sum = np.sum(data[outlier_mask])
            #if outlier_sum > 0: continue

            masked_data = data.reshape(-1)[flat_data_mask]
            dataarray.append(masked_data[np.newaxis,:])
            images_used.append(labelfile)

        _ = fileh.create_array(fileh.root,'files'       ,images_used)
        _ = fileh.create_array(fileh.root,'volmask'     ,rawfileh.root.mask.read())
        _ = fileh.create_array(fileh.root,'datamask'    ,flat_data_mask)
        _ = fileh.create_array(fileh.root,'cropbbox_min',rawfileh.root.cropbbox_min.read()) 
        _ = fileh.create_array(fileh.root,'cropbbox_max',rawfileh.root.cropbbox_max.read()) 

        print "Loading data into {}".format(datafile)
        print "# images loaded:",len(images_used)
        print "Data file: ", datafile
    else:
        print "Data file {} exists. Not loading.".format(datafile)
    print 

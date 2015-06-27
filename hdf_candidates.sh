#!/bin/bash
# Push all canddiate labels into hdf5
 
tar=$1
lblval=$2
dest=$3
tmp=$(mktemp -d)

filestem=$(basename $tar .tar)

tar -C $tmp -xf $tar 

filedir=$(dirname $(find $tmp -name '*.mnc' | head -n1))
./hdfify.py mask.mnc ${lblval} $filedir $dest
rm -rf $tmp 

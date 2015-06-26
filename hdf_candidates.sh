#!/bin/bash
# Push all canddiate labels into hdf5
 
tar=$1
dest=$2
tmp=$(mktemp -d)

filestem=$(basename $tar .tar)

tar -C $tmp -xf $tar 

filedir=$(dirname $(find $tmp -name '*.mnc' | head -n1))
./hdfify.py --mask mask.mnc $filedir $dest
rm -rf $tmp 

#!/bin/bash
# Push all canddiate labels into hdf5
 
tar=$1
dest=$2
tmp=$(mktemp -d)

tar -C $tmp -xf $tar 

filedir=$(dirname $(find $tmp -name '*.mnc' | head -n1))
./voxel_vote.py $filedir/*.mnc $dest
rm -rf $tmp 

#!/bin/bash
# Transforms candidate labels in a tarbal
 
tar=$1
dest=$2
tmp=$(mktemp -d)

filestem=${tar/*ADNI/ADNI}
filestem=${filestem/_everything.tar/}

tar -C $tmp -xf $tar 

xfm=reg_images/${filestem}.xfm
model=/opt/quarantine/CIVET/1.1.12/build/share/mni-models/mni_adni_t1w_tal_nlin_asym.mnc
regtmp=$(mktemp -d)

i=0
find $tmp -name '*.mnc' | while read lbl; do 
  mincresample -transform $xfm \
    -quiet \
    -keep -near \
    -like $model \
    $lbl \
    $regtmp/${filestem}_${i}.mnc
  i=$(($i + 1))
done
    
tar cf $dest $regtmp
rm -rf $tmp $regtmp

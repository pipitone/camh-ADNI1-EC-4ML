#!/bin/bash
# Transforms candidate labels in a tarbal

native=$PWD/fused_labels
dest=$PWD/mni_fused

model=/opt/quarantine/CIVET/1.1.12/build/share/mni-models/mni_adni_t1w_tal_nlin_asym.mnc

for lbl in $native/*.mnc; do 
  filestem=$(basename $lbl .mnc) 
  xfm=reg_images/${filestem}.xfm
  echo mincresample -transform $xfm \
    -quiet \
    -keep -near \
    -like $model \
    $lbl \
    $dest/${filestem}.mnc
done

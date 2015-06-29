A project to prepare Entorhinal Cortex segmentations of ADNI images for machine
learning applications. 

Registered images:  /projects/nikhil/EC_data/mni_registered_data
Segmentations: /projects/nikhil/EC_data/CompleteADNIScreeningData

 - candidate_labels/ - a copy of all tarballs from nikhil
 - mni_candidates - candidate labels in mni space
 - mni_fused - fused labels in mni space

## Prepare candidate labels

  mkdir candidate_labels 
  cp -s /projects/nikhil/EC_data/CompleteADNIScreeningData/batch*/* \
    candidate_labels/

## Transforming candidate labels into mni space: 

  mkdir mni_candidates
  # loop over each tarball, resample, and tar
  for i in candidate_labels/*.tar; do 
    echo ./transform_candidates.sh $i mni_candidates/$(basename $i); 
  done | parallel -j24

## Transforming fused labels into mni space: 

  mkdir mni_fused
  ./transform_fused.sh | parallel -j24
  

## Get bounding box for candidate labels

  mincmath -max -quiet mni_fused/* mask.mnc

## Convert labels to hdf5 (and crop)

  ./hdfify.py mask.mnc 1 mni_fused/ fused_labels_l.h5
  ./hdfify.py mask.mnc 2 mni_fused/ fused_labels_r.h5

  mkdir mni_candidates_{l,r}
  for i in mni_candidates/*.tar; do 
    echo ./hdf_candidates.sh $i 1 mni_candidates_l/$(basename $i .tar)_l.h5; 
    echo ./hdf_candidates.sh $i 2 mni_candidates_r/$(basename $i .tar)_r.h5; 
  done  | parallel -j24

  ./hdfmerge.py mni_candidates_l/ candidate_labels_l.h5
  ./hdfmerge.py mni_candidates_r/ candidate_labels_r.h5

## Remove outlier labels, flatten, and drop mostly empty voxels

  ./remove_outliers.py candidate_labels_l.h5 cleaned_candidate_labels_l.h5
  ./remove_outliers.py candidate_labels_r.h5 cleaned_candidate_labels_r.h5

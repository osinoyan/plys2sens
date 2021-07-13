#!/bin/bash
## bash save_model.sh [model_name]

mkdir $1

mv model.ckpt* $1/
mv graph.pbtxt $1/
mv events.* $1/
mv checkpoint $1/

# cp ../tof_FT3_mean_l1_size384/model.ckpt-200000* . 
# cp ../tof_FT3_mean_l1_size384/checkpoint . 
# cp ../tof_FT3_mean_l1_size384/graph.pbtxt . 
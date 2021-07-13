#!/usr/bin/fish

rm model.ckpt* graph.pbtxt events.* checkpoint
cp ../tof_FT3_mean_l1_size384/model.ckpt-200000* . 
cp ../tof_FT3_mean_l1_size384/checkpoint . 
cp ../tof_FT3_mean_l1_size384/graph.pbtxt . 
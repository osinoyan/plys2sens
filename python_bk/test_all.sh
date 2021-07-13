#!/bin/bash

# if [ "$1" = "NOMAXDEP" ]
# then
#     cp dataset_no_max_dep.py dataset.py
# elif [ "$1" = "MAXDEP" ]
# then
#     cp dataset_max_dep.py dataset.py
# fi

python start.py -b 2\
 --modelName sample_pyramid_add_kpn\
  --postfix size384 --lossMask depth_kinect_with_gt_msk\
   --lr 0.0004 --trainingSet yee --imageShape 350 450\
    --lossType mean_l1 --addGradient sobel_gradient\
     --gpuNumber 4 --evalSteps 1200\
      --flagMode test_all --checkpointSteps $1\
        # --dataset $2
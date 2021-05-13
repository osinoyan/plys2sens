#!/usr/bin/fish


python start.py -b 2\
 --modelName sample_pyramid_add_kpn\
  --postfix size384 --lossMask depth_kinect_with_gt_msk\
   --lr 0.0004 --trainingSet yee --imageShape 350 450\
    --lossType mean_l1 --addGradient sobel_gradient\
     --gpuNumber 4 --evalSteps 1200\
      --flagMode eval_ED --checkpointSteps 250000

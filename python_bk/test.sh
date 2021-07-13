#!/usr/bin/fish

# python start.py -b 2\
#  --steps 200000 --modelName sample_pyramid_add_kpn\
#   --postfix size384 --lossMask depth_kinect_with_gt_msk\
#    --lr 0.0004 --trainingSet tof_FT3 --imageShape 480 640\
#     --lossType mean_l1 --addGradient sobel_gradient\
#      --gpuNumber 0 --evalSteps 1200\
#       --flagMode test --checkpointSteps 200000

## TESTING ---------------------------------------------

python start.py -b 2\
 --modelName sample_pyramid_add_kpn\
  --postfix size384 --lossMask depth_kinect_with_gt_msk\
   --lr 0.0004 --trainingSet yee --imageShape 350 450\
    --lossType mean_l1 --addGradient sobel_gradient\
     --gpuNumber 4 --evalSteps 1200\
      --flagMode test_EVAL --checkpointSteps $1

## TRAINING ---------------------------------------------

# python start.py --batchSize 2\
#  --steps 300000 --modelName sample_pyramid_add_kpn\
#   --postfix size384 --lossMask depth_kinect_with_gt_msk\
#    --lr 0.0004 --trainingSet yee --imageShape 350 450\
#     --lossType mean_l1 --addGradient sobel_gradient\
#      --gpuNumber 4\
#       --flagMode train --checkpointSteps 200000
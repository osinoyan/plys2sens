#!/usr/bin/fish
LC_TIME=en_US.utf8

STIME=$(date)
echo $STIME
python write_record_gt.py SensReader/$1.dmp SensReader/$1.ply.GTA.dmp

echo $STIME
date





##   LAB05 ---- 5K
# python start.py --batchSize 2\
#  --steps 205000 --modelName sample_pyramid_add_kpn\
#   --postfix size384 --lossMask depth_kinect_with_gt_msk\
#    --lr 0.04 --trainingSet yee --imageShape 350 450\
#     --lossType mean_l1 --addGradient sobel_gradient\
#      --gpuNumber 4\
#       --flagMode train\
#         --dataset lab05 

##   BOOKCASE ---- 200K-210K
# python start.py --batchSize 2\
#  --steps 210000 --modelName sample_pyramid_add_kpn\
#   --postfix size384 --lossMask depth_kinect_with_gt_msk\
#    --lr 0.04 --trainingSet yee --imageShape 350 450\
#     --lossType mean_l1 --addGradient sobel_gradient\
#      --gpuNumber 4\
#       --flagMode train\
#         --dataset bookcase

##   CORNER ---- 210K-220K
# python start.py --batchSize 2\
#  --steps 220000 --modelName sample_pyramid_add_kpn\
#   --postfix size384 --lossMask depth_kinect_with_gt_msk\
#    --lr 0.04 --trainingSet yee --imageShape 350 450\
#     --lossType mean_l1 --addGradient sobel_gradient\
#      --gpuNumber 4\
#       --flagMode train\
#         --dataset corner 

##   DESK ---- 5K
# python start.py --batchSize 2\
#  --steps 220000 --modelName sample_pyramid_add_kpn\
#   --postfix size384 --lossMask depth_kinect_with_gt_msk\
#    --lr 0.04 --trainingSet yee --imageShape 350 450\
#     --lossType mean_l1 --addGradient sobel_gradient\
#      --gpuNumber 4\
#       --flagMode train\
#         --dataset desk 

#   TWOBOXES ---- 220K-230K
# python start.py --batchSize 2\
#  --steps 230000 --modelName sample_pyramid_add_kpn\
#   --postfix size384 --lossMask depth_kinect_with_gt_msk\
#    --lr 0.04 --trainingSet yee --imageShape 350 450\
#     --lossType mean_l1 --addGradient sobel_gradient\
#      --gpuNumber 4\
#       --flagMode train\
#         --dataset twoboxes 

##   TOF_FT3 ---- 5K
# python start.py --batchSize 2\
#  --steps 220000 --modelName sample_pyramid_add_kpn\
#   --postfix size384 --lossMask depth_kinect_with_gt_msk\
#    --lr 0.04 --trainingSet tof_FT3 --imageShape 350 450\
#     --lossType mean_l1 --addGradient sobel_gradient\
#      --gpuNumber 4\
#       --flagMode train\
#         --dataset tof_ft3 
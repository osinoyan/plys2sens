#!/bin/bash
# bash run.sh cloop00
LC_TIME=en_US.utf8

date
./conver2dmp data/$1 $1.dmp
date
./reader recording_$1.sens pose_$1
date
./binply2dmp $1.ply pose_$1
date

# mv $1.ply.GTA.dmp dmp_gt/
# mv $1.dmp dmp_noisy/

# arr=("cloop000" "cloop00" "cp01" "cp02" "cp03" "cp04" "cp05" "cpall")
#  arr=("LV00" "LV01" "LV02" "LV03" "LV07" "LV08" "LV09" "LVC0")
# arr=("LVE0" "LV11" "LV12" "LV13" "LV14")
# arr=("LV00" "LV01" "LV02" "LV03" "LV07" "LV08" "LV09" "LVC0" "LV11" "LV12" "LV13" "LV14")
# arr=("RM00" "RM01" "RM02" "RM04" "RM05" "RM06" "RM07" "RM08" "RM09" "RM10" "RMC0" "RM11" "RMC0")

# date
# for ((i=0; i < ${#arr[@]}; i++))
# do
#     date
#     ./conver2dmp data/${arr[$i]} ${arr[$i]}.dmp
#     date
#     ./reader recording_${arr[$i]}.sens pose_${arr[$i]}
#     date
#     ./binply2dmp ${arr[$i]}.ply pose_${arr[$i]}
#     date
     
#     # bash sens.sh ${arr[$i]}

#     mv ${arr[$i]}.ply.GTA.dmp dmp_gt/
#     mv ${arr[$i]}.dmp dmp_noisy/
# done






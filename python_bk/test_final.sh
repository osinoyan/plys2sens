#!/usr/bin/bash
LC_TIME=en_US.utf8
# bash test_final.sh FINAL 202480 EE02 SRF10E
# TIME=$(date +%T)

PTSET=$1

MODEL_STEP=$2
TSET=$3
MODEL_FLAG=$4

cd ../datasets/tfrecords/yee
rm -rf zzzz*
touch zzzz___$TSET
# SAVE $1
mkdir $PTSET
mv yee*.tfrecords $PTSET
# READ $2
mv $TSET/* .


cd ../../../pipe
bash test.sh $MODEL_STEP

mv ypre/00000 "ypre/${TSET}_${MODEL_FLAG}"

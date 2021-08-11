#!/usr/bin/bash
LC_TIME=en_US.utf8

rm -rf zzzz*
touch zzzz___$2
# SAVE $1
mkdir $1
mv yee*.tfrecords $1
# READ $2
mv $2/* .
# mv $2 $2_EMPTY
# mv $2_EMPTY/* .

# if [ "$1" = "READ" ]
# then
#     echo "READ $2"
#     mv $2 $2_EMPTY
#     mv $2_EMPTY/* .
# elif [ "$1" = "SAVE" ]
# then
#     echo "READ $2"
#     mv $2_EMPTY $2
#     mv yee*.tfrecords $2
# fi

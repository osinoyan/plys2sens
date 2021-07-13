#!/bin/bash
LC_TIME=en_US.utf8

date

./binply2dmp $1.ply pose_$1

date
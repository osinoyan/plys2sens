#!/bin/bash
## bash dmp.sh [EE00]

LC_TIME=en_US.utf8

date
./conver2dmp data/$1 $1.dmp
date


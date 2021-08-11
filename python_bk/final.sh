#!/usr/bin/bash
LC_TIME=en_US.utf8

STEP=$1

bash test_final.sh FINAL_PLUS  $STEP EE02 SRP10E
bash test_final.sh EE02  $STEP EE07 SRP10E
bash test_final.sh EE07  $STEP EE08 SRP10E
bash test_final.sh EE08  $STEP EE11 SRP10E
bash test_final.sh EE11  $STEP EE03 SRP10E
bash test_final.sh EE03  $STEP EE04 SRP10E
bash test_final.sh EE04  $STEP EE06 SRP10E
bash test_final.sh EE06  $STEP EE09 SRP10E
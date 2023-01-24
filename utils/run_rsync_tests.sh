#!/bin/bash

# Transfer files created by setup_rsync_tests
destination=usercontainer
user=$PW_USER

for file in $( ls test_*.bin | head -10 )
do
    rsync $file $user@$destination:/pw/tmp/ &
done


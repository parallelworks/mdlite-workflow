#!/bin/bash

# Transfer files created by setup_rsync_tests
destination=usercontainer
user=$PW_USER

for file in $( ls test_*.bin )
do
    echo Working on $file
    # Head node example
    #rsync $file $destination:/pw/tmp_sfg/ &
    # Worker node example - need to insert 
    # internal IP of head node with -J!
    rsync -avzq  -e 'ssh -J 10.3.14.210' $file $destination:/pw/tmp_sfg/ &
done


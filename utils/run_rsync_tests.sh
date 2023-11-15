#!/bin/bash

# Transfer files created by setup_rsync_tests
destination=usercontainer
user=$PW_USER
head_node_ip="10.128.0.49"

for file in $( ls test_*.bin )
do
    echo Working on $file
    # Head node example
    #rsync $file $destination:/pw/tmp_sfg/ &
    # Worker node example - need to insert 
    # internal IP of head node with -J!
    cmd="ssh -J $head_node_ip $destination exit; rsync -avzq  -e 'ssh -J $head_node_ip' $file $destination:/pw/tmp_sfg/ &"

    echo Running $cmd

    $($cmd)
done


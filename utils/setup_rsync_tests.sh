#!/bin/bash

# Create a bunch of files
for num in {101..120}
do
    fn=test_${RANDOM}_${num}.bin
    # Some systems don't allow using fallocate
    #fallocate -l 10MB ${fn}
    # dd alternative
    #dd if=/dev/zero of=${fn} bs=1M seek=10 count=0
    echo $RANDOM >> ${fn}
done


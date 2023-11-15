#!/bin/bash

# Create a bunch of files
for num in {101..120}
do
    fn=test_${RANDOM}_${num}.bin
    # Some systems don't allow using fallocate
    #fallocate -l 10MB ${fn}
    # dd alternative
    # Set bs=1M and seek=10 => 1x10 = ~10MB files
    dd if=/dev/zero of=${fn} bs=10M seek=10 count=0
    echo $RANDOM >> ${fn}
done


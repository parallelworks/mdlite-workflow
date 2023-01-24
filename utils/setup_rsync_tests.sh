#!/bin/bash

# Create a bunch of files
for num in {101..120}
do
    fallocate -l 10MB test_$RANDOM_${num}.bin
    echo $RANDOM >> test_${RANDOM}_${num}.bin
done


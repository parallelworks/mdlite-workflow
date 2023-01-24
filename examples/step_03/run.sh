#!/bin/bash
#----------------------------
# Sample run script for local
# run of this workflow step.
#----------------------------

# Link run script and executable
# to here so all inputs and outputs
# are kept in this folder.
cp ../../models/c-ray/renderframe ./
cp ../../models/c-ray/c-ray ./

# Link to input files from previous
# step
cp ../step_02/trjout.tmp ./
cp ../step_02/metricout.tmp ./

# Run
./renderframe metricout.tmp out.png 0

# Clean up links so they are not git tracked.
rm renderframe
rm c-ray
rm trjout.tmp
rm metricout.tmp

#!/bin/bash
#----------------------------
# Sample run script for local
# run of this workflow step.
#----------------------------

# Link run script and executable
# to here so all inputs and outputs
# are kept in this folder.
ln -sv ../../models/mdlite/runMD.sh ./
ln -sv ../../models/mdlite/md ./

# Run
./runMD.sh "mass,0.01|npart,25|steps,3000|trsnaps,10" trjout.tmp metricout.tmp

# Clean up links so they are not git tracked.
rm runMD.sh
rm md

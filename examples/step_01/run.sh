#!/bin/bash
#----------------------------
# Sample run script for local
# run of this workflow step.
#----------------------------

# Python requires execution to
# be references to the directory
# that holds the code if modules
# from that directory are to be
# loaded. (I.e. Copying prepinputs.py
# to here and running it like
# python prepinputs.py will not work.)

python ../../models/mexdex/prepinputs.py params.run out.tmp

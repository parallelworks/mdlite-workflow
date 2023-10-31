#!/bin/bash
set -x

# Grab current version of parsl_utils
# or specify branch with -b
git clone https://github.com/parallelworks/parsl_utils.git parsl_utils

#--------------------------------------------
# Convert Jupyter notebook to main.py
#--------------------------------------------
# (.py is automatically appended to output!)
#jupyter nbconvert --log-level 0 --to script --output main main.ipynb

# NOTE: The above is disabled since the default
# PW Conda environment does not currently have
# Jupyter pre-installed. To bypass this, a main.py
# is saved in this repository but it will need to
# be manually synced with main.ipynb.

#-------------------------------------------
# Configuration files
#-------------------------------------------

# WORKING HERE - Commenting all this out to
# test storage/transfer of this information in
# the workflow.xml instead of the local.conf
# and executors.json.

# If not present, use default local.conf and executors.json
#if [ ! -f "local.conf" ]; then
#    echo Using default local.conf...
#    cp ./examples/local.conf.example ./local.conf
#fi
#source local.conf

#if [ ! -f "executors.json" ]; then
#    echo Using default executors.json...
#    cp ./examples/executors.json.example ./executors.json
#fi

#------------------------------------------
# Launch!
#------------------------------------------
# Cannot run scripts inside parsl_utils directly
bash parsl_utils/main.sh $@


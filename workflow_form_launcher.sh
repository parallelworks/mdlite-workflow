#!/bin/bash
set -x

# Grab current version of parsl_utils
git clone -b dev https://github.com/parallelworks/parsl_utils.git parsl_utils

# Convert Jupyter notebook to main.py
jupyter nbconvert --log-level 0 --to script --output main.py main.ipynb

# Cannot run scripts inside parsl_utils directly
bash parsl_utils/main.sh $@


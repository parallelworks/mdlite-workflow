#!/bin/bash
#===========================
# Download Miniconda, install,
# and create a new environment
# for using MDLite.
#
# With a fast internet connection
# (i.e. download time minimal)
# this process takes ~2 min and
# results in a 2.2GB Conda env.
#
# For moving conda envs around,
# it is possible to put the
# miniconda directory in a tarball
# but the paths will need to be
# adjusted.  The download and
# decompression time can be long.
# As an alternative, consider:
# conda list -e > requirements.txt
# to export a list of the req's
# and then:
# conda create --name <env> --file requirements.txt
# to build another env elsewhere.
# This second step runs faster
# than this script because
# Conda does not stop to solve
# the environment.  Rather, it
# just pulls all the listed
# packages assuming everything
# is compatible.
#===========================

# Get username
my_username=$(whoami)

# Miniconda install location
# The `source` command somehow
# doesn't work with "~", so best
# to put an absolute path here
# if putting Miniconda in $HOME.
miniconda_loc="/home/${my_username}/pw/miniconda"
echo Will install to $miniconda_loc

# Ensure that the beginning of the path
# for the install location already exists.
echo Creating/ensuring $(dirname $miniconda_loc) exists...
mkdir -p $(dirname $miniconda_loc)

# Download current version of
# Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Run Miniconda installer
chmod u+x ./Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh -b -p $miniconda_loc

# Clean up
rm ./Miniconda3-latest-Linux-x86_64.sh

# Define environment name.  Base is
# the default.  You can define other
# envs with different names for testing
# or running multiple workflows on the
# same resource.
my_env="mdlite"

# Define specific versions here
# or leave blank to use whatever
# is automatically selected.
python_version="=3.7"
parsl_version="==1.2"

#======================================
# Version adjustment
#======================================
# Try current versions of everything!
python_version=""
parsl_version=""

# Start conda
source ${miniconda_loc}/etc/profile.d/conda.sh
conda activate base

# Create new environment
# We are running Jupter notebooks so include ipython here.
if [[ $my_env == "base" ]]
then
    conda install -y ipython
else
    conda create -y --name $my_env python${python_version} ipython

    # Jump into new environment
    conda activate $my_env
fi

# Install packages
conda install -y requests
conda install -y ipykernel
conda install -y -c anaconda jinja2
conda install -y -c conda-forge jupyter
conda install -y -c conda-forge parsl
conda install -y -c conda-forge numpy
conda install -y -c conda-forge pandas
conda install -y -c conda-forge matplotlib

# Write out the requirements.txt to document environment
conda list -e > requirements.txt

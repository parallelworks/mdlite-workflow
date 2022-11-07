#!/bin/bash
#=================================
# Design Explorer (DEX) must have
# absolute paths to work. So, in 
# order to move DEX data from 
# place to place, the paths need
# to be changed in the *.html and
# *.csv file associated with the
# data set.
#
# This script will modify the paths
# in the *.html and *.csv files.
# The input is:
# $1 = basename of the *.html and 
#      *.csv files.
# $2 = the original (current) path
# $3 = what the path should be changed
#      to with a direct sed search
#      and replace.
#
# $2 and $3 should be used as 
# dirnames; i.e. the prefix of the
# path that needs to change.
#
# For example, if the original paths are:
# /home/user/mdlite-workflow
# and we want to change them to
# /pw/clusters/pool/mdlite-workflow
# then the invocation is:
#
# change_dex_result_paths.sh mdlite_dex /home/user/ /pw/clusters/pool/
#================================

#================================
# CLI inputs
# Run basename twice in case the .html or .csv file
# is specified on command line via tab completion
dex_bname_tmp=$(basename $1 .html)
dex_bname=$(basename $dex_bname_tmp .csv)
dex_path_1=$2
dex_path_2=$3

# Filter for sed
dex_path_1_for_sed=$(echo $dex_path_1 | sed 's/\//\\\//g')
dex_path_2_for_sed=$(echo $dex_path_2 | sed 's/\//\\\//g')

# Cross check
echo Working on ${dex_bname}.html and ${dex_bname}.csv
echo Initial path: $dex_path_1 sed filter: $dex_path_1_for_sed
echo Final path: $dex_path_2 sed filter: $dex_path_2_for_sed

#===============================
# Make bkup copies and filter

mv ${dex_bname}.html ${dex_bname}.html.old
mv ${dex_bname}.csv ${dex_bname}.csv.old

sed "s/$dex_path_1_for_sed/$dex_path_2_for_sed/g" ${dex_bname}.html.old > ${dex_bname}.html
sed "s/$dex_path_1_for_sed/$dex_path_2_for_sed/g" ${dex_bname}.csv.old > ${dex_bname}.csv

# Done!

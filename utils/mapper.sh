#!/bin/bash

rootdir=
if [ "$1" == "-root" ]; then
    rootdir=$2
else
    echo "Invalid parameter: $1"
    exit 1
fi

filelist=$(find $rootdir -type f)

counter=0

for ff in $filelist
do
	echo "[$counter] $ff"
	let counter=counter+1
done

#!/bin/bash
#first serial, then mpi
#if [ -z "$(echo \"$*\" |grep np)" ];then
#    sudo docker run -u $(id -u):$(id -g) -v $PWD:/data nwchemorg/nwchem-dev $*
#if [ -z "$1" ];then
#echo "Example: $0 h2o.nw"
#exit
#fi
docker run -u $(id -u):$(id -g) -v $PWD:/data nwchemorg/nwchem-dev $*

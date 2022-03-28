#!/bin/bash

# USAGE:
# - CalculiX (exo file):
#    ./extract.sh /opt/paraview530/bin utils/extract.py sample_inputs/solve.exo sample_inputs/beadOnPlateKPI.json example_outputs example_outputs/metrics.csv 
# - openFOAM:
#    ./extract.sh /opt/paraview530/bin utils/extract.py sample_inputs/elbow-test/system/controlDict sample_inputs/elbowKPI.json example_outputs/openFOAM/ example_outputs/openFOAM/metrics.csv 

paraviewPath=$1
pvpythonExtractScript=$2
resultsFile=$3
desiredMetricsFile=$4
pvOutputDir=$5
outputMetrics=$6

export PATH=$PATH:$paraviewPath

xvfb-run -a --server-args="-screen 0 1024x768x24" pvpython  --mesa-llvm   $pvpythonExtractScript  $resultsFile $desiredMetricsFile  $pvOutputDir $outputMetrics



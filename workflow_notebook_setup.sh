#!/bin/bash
set -x

# Grab current version of parsl_utils
git clone -b dev https://github.com/parallelworks/parsl_utils.git parsl_utils

# If not present, use default local.conf and executors.json
if [ ! -f "local.conf" ]; then
    echo Using default local.conf...
    cp ./examples/local.conf.example ./local.conf
fi

if [ ! -f "executors.json" ]; then
    echo Using default executors.json...
    cp ./examples/executors.json.example ./executors.json
fi

# Setup parsl_utils (based on preamble of parsl_utils/main.sh)
#bash parsl_utils/main.sh $@
pudir=parsl_utils #$(dirname $0)
. ${pudir}/utils.sh

# Copy the kill file
cp parsl_utils/kill.sh ./

# Clear logs
mkdir -p logs
rm -rf logs/*

# replace the executors file if an override exists
if [ -f "executors.override.json" ];then
    cp executors.override.json executors.json
fi

# check if executors file exists
if [ ! -f executors.json ]; then
    echo "ERROR: File executors.json is missing; workflow does not know where to run!"
    echo "This missing file should have at least the following information for at"
    echo "least one executor (multiple executors are optional):" 
    echo "{"
    echo "  \"myexecutor_1\": {"
    echo "    \"POOL\": \"<pw_resource_name>\","
    echo "    \"PROVIDER_TYPE\": \"LOCAL\","
    echo "    \"CONDA_ENV\": \"<conda_env_name>\","
    echo "    \"CONDA_DIR\": \"__POOLWORKDIR__/pw/.miniconda3\","
    echo "    \"CORES_PER_WORKER\": <integer_or_fractional_number_cores>,"
    echo "    \"INSTALL_CONDA\": \"<true|false>\","
    echo "    \"LOCAL_CONDA_YAML\": \"./requirements/conda_env_remote.yaml\","
    echo "    \"SlurmProvider\": {"
    echo "      \"partition\": \"<partition_name>\","
    echo "      \"nodes_per_block\": <integer>,"
    echo "      \"cores_per_node\": <integer>,"
    echo "      \"min_blocks\": <integer>,"
    echo "      \"max_blocks\": <integer>,"
    echo "      \"walltime\": \"01:00:00\""
    echo "    }"
    echo "  },"
    echo "  \"myexecutor_2\": {...},"
    echo "  ..."
    echo "}"
    echo "The \"SlurmProvider\" section is ommitted if the executor is not a SLURM cluster."
    exit 1
fi

# Use a job_number to:
# 1. Track / cancel job
# 2. Stage temporary files
job_number=$(basename ${PWD})   #job-${job_num}_date-$(date +%s)_random-${RANDOM}
wfargs="$@ --job_number ${job_number}"

# Replace special placeholders:
wfargs="$(echo ${wfargs} | sed "s|__job_number__|${job_number}|g")"
sed -i "s|__job_number__|${job_number}|g" executors.json
sed -i "s|__job_number__|${job_number}|g" kill.sh

#########################################
# CHECKING AND PREPARING USER CONTAINER #
#########################################
# - Not required if running a notebook since the kernel would be changed to this environment

############################################
# CHECKING AND PREPRARING REMOTE EXECUTORS #
############################################
bash ${pudir}/prepare_resources.sh ${job_number} &> logs/prepare_resources.out

###############################
# CREATE MONITORING HTML FILE #
###############################
sed "s/__JOBNUM__/${job_number}/g" ${pudir}/service.html.template > service.html

####################
# SUBMIT PARSL JOB #
####################
# - Not required if running from a notebook since submission is manual

##########################
# CLEAN REMOTE EXECUTORS #
##########################
# - Not required if running from a notebook since clean up is manual (from notebook)

##########################
# Exit                   #
##########################
# - Not required if running from a notebook since exit is manual


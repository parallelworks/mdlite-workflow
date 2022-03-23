


export CORES=$(getconf _NPROCESSORS_ONLN)

echo "Found cores : $CORES"

WORKERCOUNT=1

export keepSiteDir=false

CONDA_BASE=$PWD/.miniconda3
source $CONDA_BASE/etc/profile.d/conda.sh

conda activate $CONDA_ENV

taskport=$(echo "process_worker_pool.py   -p 0 -c 1 -m None --poll 1000 --task_url=tcp://127.0.0.1:54550 --result_url=tcp://127.0.0.1:54995 --logdir=/pw/workflows/my_workflow/runinfo/000/coaster_single_node --block_id=0 --hb_period=30 --hb_threshold=120 " | grep -Po  "task_url=\K(.*)(?= --result_url)" | cut -d ':' -f3)
resultport=$(echo "process_worker_pool.py   -p 0 -c 1 -m None --poll 1000 --task_url=tcp://127.0.0.1:54550 --result_url=tcp://127.0.0.1:54995 --logdir=/pw/workflows/my_workflow/runinfo/000/coaster_single_node --block_id=0 --hb_period=30 --hb_threshold=120 " | grep -Po  "result_url=\K(.*)(?= --logdir)" | cut -d ':' -f3)

echo $taskport $resultport

cmd="process_worker_pool.py   -p 0 -c 1 -m None --poll 1000 --task_url=tcp://127.0.0.1:54550 --result_url=tcp://127.0.0.1:54995 --logdir=/pw/workflows/my_workflow/runinfo/000/coaster_single_node --block_id=0 --hb_period=30 --hb_threshold=120 "
# adjust the worker count to always = nproc so we only spawn one parsl worker per node

cmd=$(echo $cmd | sed "s/-c.*-m/-c $CORES -m/")

echo $cmd

userhost="$PW_USER_HOST"
echo ssh -L 0.0.0.0:$taskport:0.0.0.0:$taskport -L 0.0.0.0:$resultport:0.0.0.0:$resultport $userhost-container -fNT
ssh -L 0.0.0.0:$taskport:0.0.0.0:$taskport -L 0.0.0.0:$resultport:0.0.0.0:$resultport $userhost-container -fNT

# start the new parsl tunnels
#if [[ "$connecthost" == "localhost" ]];then
#    ssh -L $taskport:$connecthost:$taskport localhost -fNT
#    ssh -L $resultport:$connecthost:$resultport localhost -fNT
#fi

CMD ( ) {
$cmd
}
for COUNT in $(seq 1 1 $WORKERCOUNT)
do
    echo "Launching worker: $COUNT at $(date)"
    # CMD & # FIXME: EXPERIMENT
    CMD     # FIXME: EXPERIMENT - no & here; higher level
done

# wait                       # FIXME: moved wait to higher level shell # FIXME: EXPERIMENT
                             # FIXME: with & disabled above, higher level shell forks this off # FIXME: EXPERIMENT
echo "All workers launched at $(date)" # MJW


from parsl.config import Config
from parsl.channels import SSHChannel
from parsl.providers import LocalProvider, SlurmProvider
from parsl.executors import HighThroughputExecutor
#from parsl.monitoring.monitoring import MonitoringHub
from parsl.addresses import address_by_hostname
import os,json
import argparse

def read_args():
    parser=argparse.ArgumentParser()
    parsed, unknown = parser.parse_known_args()
    for arg in unknown:
        if arg.startswith(("-", "--")):
            parser.add_argument(arg)
    pwargs=vars(parser.parse_args())
    print(pwargs)
    return pwargs

with open('executors.json', 'r') as f:
    exec_conf = json.load(f)

for label,executor in exec_conf.items():
    for k,v in executor.items():
        if type(v) == str:
            exec_conf[label][k] = os.path.expanduser(v)

# Add sandbox directory
for exec_label, exec_conf_i in exec_conf.items():
    if 'RUN_DIR' in exec_conf_i:
        exec_conf[exec_label]['RUN_DIR'] = os.path.join(exec_conf_i['RUN_DIR'])
    else:
        base_dir = '/tmp'
        exec_conf[exec_label]['RUN_DIR'] = os.path.join(base_dir, str(job_number))

config = Config(
    executors = [
        HighThroughputExecutor(
            worker_ports = ((int(exec_conf['myexecutor_1']['WORKER_PORT_1']), int(exec_conf['myexecutor_1']['WORKER_PORT_2']))),
            label = 'myexecutor_1',
            worker_debug = True,             # Default False for shorter logs
            cores_per_worker = float(exec_conf['myexecutor_1']['CORES_PER_WORKER']), # One worker per node
            worker_logdir_root = exec_conf['myexecutor_1']['WORKER_LOGDIR_ROOT'],  #os.getcwd() + '/parsllogs',
            address = exec_conf['myexecutor_1']['ADDRESS'],
            provider = SlurmProvider(
                partition = exec_conf['myexecutor_1']['PARTITION'],
                nodes_per_block = int(exec_conf['myexecutor_1']['NODES']),
                cores_per_node = int(exec_conf['myexecutor_1']['NTASKS_PER_NODE']),
                min_blocks = int(exec_conf['myexecutor_1']['MIN_BLOCKS']),
                max_blocks = int(exec_conf['myexecutor_1']['MAX_BLOCKS']),
                walltime = exec_conf['myexecutor_1']['WALLTIME'],
                worker_init = 'source {conda_sh}; conda activate {conda_env}; cd {run_dir}'.format(
                    conda_sh = os.path.join(exec_conf['myexecutor_1']['CONDA_DIR'], 'etc/profile.d/conda.sh'),
                    conda_env = exec_conf['myexecutor_1']['CONDA_ENV'],
                    run_dir = exec_conf['myexecutor_1']['RUN_DIR']
                ),
                channel = SSHChannel(
                    hostname = exec_conf['myexecutor_1']['HOST_IP'],
                    username = exec_conf['myexecutor_1']['HOST_USER'],
                    script_dir = exec_conf['myexecutor_1']['SSH_CHANNEL_SCRIPT_DIR'], # Full path to a script dir where generated scripts could be sent to
                    key_filename = '/home/{PW_USER}/.ssh/pw_id_rsa'.format(PW_USER = os.environ['PW_USER'])
                )
            )
        )
    ]
)

#,
#    monitoring = MonitoringHub(
#       hub_address = address_by_hostname(),
#       resource_monitoring_interval = 5
#   )
#)

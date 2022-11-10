from parsl.config import Config
from parsl.channels import SSHChannel
from parsl.providers import LocalProvider, SlurmProvider
from parsl.executors import HighThroughputExecutor
#from parsl.monitoring.monitoring import MonitoringHub
from parsl.addresses import address_by_hostname
import os,json,argparse,subprocess

debug = False

def bash(script,*args,checkrc=False,debug=False):

    cmd = ['bash', '-s', *args]

    result = subprocess.run(cmd, input=script, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
    if debug: print('DB: bash(): subprocess.run returned: ' + str(result))

    rc = result.returncode
    if debug:  print('DB: bash(): command exit code: ' + str(rc))

    cmd_output = result.stdout
    if debug: print('DB: bash(): command output: ' + str(cmd_output))

    return (rc, cmd_output)

pw_conf      = 'pw.conf'
script = r'''
set -o pipefail
sed -e 's/{{//g;s/}}//g;s/"//g;s/: / /;s/^ +//' < {0} |
    awk '
        /^site\./   {{ gsub(/^site./,"",$1); site=$1 }}
        /  URL/     {{ print(site " " $2) }}
        '
'''.format(pw_conf)   # FIXME: Convert to python???

(rc,output) = bash(script)

selectedExecutor = None

if rc != 0:
    print('parslpw: error: can not parse parsl.swift.conf. rc={} output={}'.format(rc,output))
    selectedExecutor='googlecloud'
else:
    pools=[]
    poolinfo={}
    for line in output.splitlines():
        fields = line.split()
        poolname = fields[0]
        service = fields[1].split(':')
        host = service[1][2:] # skip over // from protocol
        port = service[2]
        pools.append(poolname)
        poolinfo[poolname]={'host':host,'port':port}
    selectedExecutor=pools[0]
    print('EXECUTOR SELECTED',selectedExecutor)

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

if 'CORES_PER_NODE' in exec_conf[selectedExecutor]:
    cores_per_node = exec_conf[selectedExecutor]['CORES_PER_NODE']
else:
    cores_per_node = None
        
config = Config(
    executors = [
        HighThroughputExecutor(
            worker_ports = ((int(exec_conf[selectedExecutor]['WORKER_PORT_1']), int(exec_conf[selectedExecutor]['WORKER_PORT_2']))),
            label = selectedExecutor,
            worker_debug = True,             # Default False for shorter logs
            cores_per_worker = float(exec_conf[selectedExecutor]['CORES_PER_WORKER']), # One worker per node
            worker_logdir_root = exec_conf[selectedExecutor]['WORKER_LOGDIR_ROOT'],  #os.getcwd() + '/parsllogs',
            address = exec_conf[selectedExecutor]['ADDRESS'],
            provider = SlurmProvider(
                partition = exec_conf[selectedExecutor]['PARTITION'],
                nodes_per_block = int(exec_conf[selectedExecutor]['NODES_PER_BLOCK']),
                cores_per_node = cores_per_node,
                min_blocks = int(exec_conf[selectedExecutor]['MIN_BLOCKS']),
                max_blocks = int(exec_conf[selectedExecutor]['MAX_BLOCKS']),
                walltime = exec_conf[selectedExecutor]['WALLTIME'],
                worker_init = 'source {conda_sh}; conda activate {conda_env}; cd {run_dir}'.format(
                    conda_sh = os.path.join(exec_conf[selectedExecutor]['CONDA_DIR'], 'etc/profile.d/conda.sh'),
                    conda_env = exec_conf[selectedExecutor]['CONDA_ENV'],
                    run_dir = exec_conf[selectedExecutor]['RUN_DIR']
                ),
                channel = SSHChannel(
                    hostname = exec_conf[selectedExecutor]['HOST_IP'],
                    username = exec_conf[selectedExecutor]['HOST_USER'],
                    script_dir = exec_conf[selectedExecutor]['SSH_CHANNEL_SCRIPT_DIR'], # Full path to a script dir where generated scripts could be sent to
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

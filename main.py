import sys, os, json, time
from random import randint
import argparse

import parsl
print(parsl.__version__, flush = True)
from parsl.app.app import python_app, bash_app
from parsl.config import Config
from parsl.channels import SSHChannel
from parsl.providers import LocalProvider
from parsl.executors import HighThroughputExecutor

import parsl_utils

with open('executors.json', 'r') as f:
    exec_conf = json.load(f)

# Apps to test Parsl

@parsl_utils.parsl_wrappers.log_app
@python_app(executors=['myexecutor_1'])
def hello_python_app_1(inputs = [], outputs = [], stdout='std.out', stderr = 'std.err'):
    import socket
    return 'Hello python_app_1 from ' + socket.gethostname()

@parsl_utils.parsl_wrappers.log_app
@python_app(executors=['myexecutor_2'])
def hello_python_app_2(inputs = [], outputs = [], stdout='std.out', stderr = 'std.err'):
    import socket
    return 'Hello python_app_2 from ' + socket.gethostname()



if __name__ == '__main__':

    # Add sandbox directory
    for exec_label, exec_conf_i in exec_conf.items():
        if 'RUN_DIR' in exec_conf_i:
            exec_conf[exec_label]['RUN_DIR'] = os.path.join(exec_conf_i['RUN_DIR'], 'run-' + str(randint(0, 99999)).zfill(5))
        else:
            base_dir = '/contrib/{PW_USER}/tmp'.format(PW_USER = os.environ['PW_USER'])
            exec_conf[exec_label]['RUN_DIR'] = os.path.join(base_dir, 'run-' + str(randint(0, 99999)).zfill(5))

    config = Config(
        executors = [
            HighThroughputExecutor(
                worker_ports = ((int(exec_conf['myexecutor_1']['WORKER_PORT_1']), int(exec_conf['myexecutor_1']['WORKER_PORT_2']))),
                label = 'myexecutor_1',
                worker_debug = True,             # Default False for shorter logs
                cores_per_worker = int(exec_conf['myexecutor_1']['CORES_PER_WORKER']), # One worker per node
                worker_logdir_root = exec_conf['myexecutor_1']['WORKER_LOGDIR_ROOT'],  #os.getcwd() + '/parsllogs',
                provider = LocalProvider(
                    worker_init = 'source {conda_sh}; conda activate {conda_env}; cd {run_dir}'.format(
                        conda_sh = os.path.join(exec_conf['myexecutor_1']['REMOTE_CONDA_DIR'], 'etc/profile.d/conda.sh'),
                        conda_env = exec_conf['myexecutor_1']['REMOTE_CONDA_ENV'],
                        run_dir = exec_conf['myexecutor_1']['RUN_DIR']
                    ),
                    channel = SSHChannel(
                        hostname = exec_conf['myexecutor_1']['HOST_IP'],
                        username = os.environ['PW_USER'],
                        script_dir = exec_conf['myexecutor_1']['SSH_CHANNEL_SCRIPT_DIR'], # Full path to a script dir where generated scripts could be sent to
                        key_filename = '/home/{PW_USER}/.ssh/pw_id_rsa'.format(PW_USER = os.environ['PW_USER'])
                    )
                )
            ),
            HighThroughputExecutor(
                worker_ports = ((int(exec_conf['myexecutor_2']['WORKER_PORT_1']), int(exec_conf['myexecutor_2']['WORKER_PORT_2']))),
                label = 'myexecutor_2',
                worker_debug = True,             # Default False for shorter logs
                cores_per_worker = int(exec_conf['myexecutor_2']['CORES_PER_WORKER']), # One worker per node
                worker_logdir_root = exec_conf['myexecutor_2']['WORKER_LOGDIR_ROOT'],  #os.getcwd() + '/parsllogs',
                provider = LocalProvider(
                    worker_init = 'source {conda_sh}; conda activate {conda_env}; cd {run_dir}'.format(
                        conda_sh = os.path.join(exec_conf['myexecutor_2']['REMOTE_CONDA_DIR'], 'etc/profile.d/conda.sh'),
                        conda_env = exec_conf['myexecutor_2']['REMOTE_CONDA_ENV'],
                        run_dir = exec_conf['myexecutor_2']['RUN_DIR']
                    ),
                    channel = SSHChannel(
                        hostname = exec_conf['myexecutor_2']['HOST_IP'],
                        username = os.environ['PW_USER'],
                        script_dir = exec_conf['myexecutor_2']['SSH_CHANNEL_SCRIPT_DIR'], # Full path to a script dir where generated scripts could be sent to
                        key_filename = '/home/{PW_USER}/.ssh/pw_id_rsa'.format(PW_USER = os.environ['PW_USER'])
                    )
                )
            )
        ]
    )

    print('Loading Parsl Config', flush = True)
    parsl.load(config)

    # Staging not supported in this test:
    fut_1 = hello_python_app_1()
    fut_2 = hello_python_app_2()

    print(fut_1.result())
    print(fut_2.result())


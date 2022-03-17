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

# Reads command line arguments in the format:
# python main.py --argkey1 argval1 --argkey2 argval2
# Returns a dictionary args in the format:
# args[argkey1] = argval1
def read_command_line_args():
    # GET COMMAND LINE ARGS FROM PW FORM
    parser = argparse.ArgumentParser()
    parsed, unknown = parser.parse_known_args()
    for arg in unknown:
        if arg.startswith(("-", "--")):
            parser.add_argument(arg)
    args = vars(parser.parse_args())
    print("\nargs:", flush=True)
    print(json.dumps(args, indent = 4), flush = True)
    return args

args = read_command_line_args()

with open(args['exec_conf'], 'r') as f:
    exec_conf = json.load(f)

# App to test Parsl
@parsl_utils.parsl_wrappers.log_app
@parsl_utils.parsl_wrappers.stage_app(exec_conf['myexecutor_1']['HOST_IP'])
@bash_app(executors=['myexecutor_1'])
def bash_app_1_staging(inputs = [], outputs = [], inputs_dict = {}, outputs_dict = {}, stdout='std.out', stderr = 'std.err'):
    import os
    import socket
    from datetime import datetime

    print(inputs_dict, flush = True)
    for ik, iv in inputs_dict.items():
        if not os.path.exists(iv['worker_path']):
            raise(Exception('Path {} does not exist'.format(iv['worker_path'])))

    print(outputs_dict, flush = True)
    for ik, iv in outputs_dict.items():
        if iv['type'] == 'file':
            with open(iv['worker_path'], 'w') as f:
                f.write(socket.gethostname() + '\n')
                f.write(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

        elif iv['type'] == 'directory':
            os.makedirs(iv['worker_path'], exist_ok = True)
            with open(os.path.join(iv['worker_path'], 'test.txt'), 'w') as f:
                f.write(socket.gethostname() + '\n')
                f.write(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

    return 'hostname'

@parsl_utils.parsl_wrappers.log_app
@parsl_utils.parsl_wrappers.stage_app(exec_conf['myexecutor_2']['HOST_IP'])
@bash_app(executors=['myexecutor_2'])
def bash_app_2_staging(inputs = [], outputs = [], inputs_dict = {}, outputs_dict = {}, stdout='std.out', stderr = 'std.err'):
    import os
    import socket
    from datetime import datetime

    print(inputs_dict, flush = True)
    for ik, iv in inputs_dict.items():
        if not os.path.exists(iv['worker_path']):
            raise(Exception('Path {} does not exist'.format(iv['worker_path'])))

    print(outputs_dict, flush = True)
    for ik, iv in outputs_dict.items():
        if iv['type'] == 'file':
            with open(iv['worker_path'], 'w') as f:
                f.write(socket.gethostname() + '\n')
                f.write(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

        elif iv['type'] == 'directory':
            os.makedirs(iv['worker_path'], exist_ok = True)
            with open(os.path.join(iv['worker_path'], 'test.txt'), 'w') as f:
                f.write(socket.gethostname() + '\n')
                f.write(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

    return 'hostname'


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

    fut_1 = bash_app_1_staging(
        inputs_dict = {
            "test_file_pw": {
                "type": "file",
                "global_path": "pw://{cwd}/test_myexecutor_1_file.txt",
                "worker_path": "{remote_dir}/test_myexecutor_1_file.txt".format(remote_dir = exec_conf['myexecutor_1']['RUN_DIR'])
            },
            "test_dir_pw": {
                "type": "directory",
                "global_path": "pw://{cwd}/test_myexecutor_1",
                "worker_path": "{remote_dir}/test_myexecutor_1".format(jupyter_lab_dir =  exec_conf['myexecutor_1']['RUN_DIR'])
            },
        },
        outputs_dict = {
            "remote_stdout": {
                "type": "file",
                "global_path": "pw://{cwd}/remote-std.out",
                "worker_path": "{remote_dir}/std.out".format(remote_dir = args['remote_dir'])
            },
            "remote_stderr": {
                "type": "file",
                "global_path": "pw://{cwd}/remote-std.err",
                "worker_path": "{remote_dir}/std.err".format(remote_dir = args['remote_dir'])
            }
        },
        stdout = 'std.out',
        stderr = 'std.err'
    )


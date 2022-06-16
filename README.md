# Single Cluster Parsl Hello World
This workflow is a "hello world" example using Parsl to connect to remote resources with the [SSHChannel](https://parsl.readthedocs.io/en/stable/stubs/parsl.channels.SSHChannel.html). It uses the [parsl_utils](https://github.com/parallelworks/parsl_utils) repository for integration with the PW platform. The purpose of this workflow is to:
1. Test new resources and resource configurations before launching more complex workflows
2. Use as template to develop more complex workflows

The workflow executes a python app and a bash app:

**Python App:**
Returns the host name of the controller node as a Python object and prints it to the standard output (`/pw/jobs/job_number/std.out`). Also returns the input parameter name.

**Bash App:**
Sends the file `./hello_srun.in` to the controller node, writes the host names of the compute nodes in it and returns it back to the job directory (`/pw/jobs/job_number/hello_srun-1.out`).

## Configuration:
The workflow configuration is defined in the files `./executors.json` and `./local.conf`:

### Executors JSON:
Defines the configuration of the remote resources and is located in the workflow's directory `/pw/workflows/workflow_name`. This file contains all the information to define the Parsl Config object in the main script. The higher level key needs to match the label parameter in the Parsl Config and in the Parsl app decorators:

```
# PARSL CONFIG
config = Config(
        executors = [
            HighThroughputExecutor(
                worker_ports = ((int(exec_conf['myexecutor_1']['WORKER_PORT_1']), int(exec_conf['myexecutor_1']['WORKER_PORT_2']))),
                label = 'myexecutor_1',
                # ...
```


```
# PARSL APP
@python_app(executors=['myexecutor_1'])
def hello_python_app_1(stdout='std.out', stderr = 'std.err'):
    # ...
```

The configuration of the executor is defined using key-value pairs. The specific key-value pairs depend on the Parsl configuration file and may change for every workflow. Also, the same workflow may use different key-value pairs, for example, to run Python in a Singularity container or a Miniconda environment. In this example:

```
{
    "myexecutor_1": {
        "POOL": "Name of the PW pool",
        "HOST_USER": "User name in the controller node. Defaults to PW user name",
        "HOST_IP": "IP of the controller node. Defaults to the IP reported by the PW API",
        "RUN_DIR": "Scratch directory for Parsl jobs and logs",
        "NODES": "Number of compute nodes",
        "PARTITION": "Name of the compute node partition",
        "NTASKS_PER_NODE": "NTASKS_PER_NODE parameter in srun command",
        "WALLTIME": "Wall time in srun command",
        "CONDA_ENV": "Name of the Conda environment in the controller node",
        "CONDA_DIR": "Path to the Conda directory in the controller node",
        "WORKER_LOGDIR_ROOT": "Path to worker log directory",
        "SSH_CHANNEL_SCRIPT_DIR": "Path to SSHChannel script directory",
        "CORES_PER_WORKER": "Number of cores per worker in the head node",
        "INSTALL_CONDA": "true or false. If true, attempts to set up the Conda environment in the controller node",
        "LOCAL_CONDA_YAML": "Local path to the Conda YAML file defining the environment. This file is used to set up the Conda environment in the controller node if INSTALL_CONDA is true"
    }
}
```

This file is completed automatically by the parsl_utils repository to include two worker ports (and the `HOST_USER` and `HOST_IP` parameters if not specified) and written to the job directory (`/pw/jobs/job_number/executors.json`)

### PW Conf:
Defines the configuration parameters of the user container in the PW account:

```
CONDA_ENV="Name of Conda environment in the user container to activate before running the main Python script."
CONDA_DIR="Path to the Conda directory in the user container"
INSTALL_CONDA="true or false. If true, attempts to set up the Conda environment in the user container"
LOCAL_CONDA_YAML="Local path to the Conda YAML file defining the environment. This file is used to set up the Conda environment in the user container if INSTALL_CONDA is true"
```

## Python Environments:
The same version of Parsl must be installed in the Python environment of the user container and of the executors. The user may set the environments manually or may use Conda YAML definition files. In this example these files are provided in the `./requirements` directory. The parsl_utils repository also supports using singularity files (instead of Conda YAML files) and singularity container (instead of Conda environments) to define the Python environment in the remote resources.

## Github
TODO
# Workflow for testing the parsl multihost on two cluster pools
To run please addapt modify the `executor.json` file below to associate the labels in the parsl configuration to the pool names in your Parallel Works account.

```
{
    "myexecutor_1": {
        "POOL": "gcpclustergen2",
        "REMOTE_CONDA_ENV": "parsl_py39",
        "REMOTE_CONDA_DIR": "/contrib/Alvaro.Vidal/miniconda3",
        "RUN_DIR": "/contrib/Alvaro.Vidal/tmp",
        "WORKER_LOGDIR_ROOT": "/contrib/Alvaro.Vidal/tmp",
        "SSH_CHANNEL_SCRIPT_DIR": "/contrib/Alvaro.Vidal/tmp",
        "CORES_PER_WORKER": 4
    },
    "myexecutor_2": {
        "POOL": "gcpcluster",
        "REMOTE_CONDA_ENV": "parsl_py39",
        "REMOTE_CONDA_DIR": "/contrib/Alvaro.Vidal/miniconda3",
        "RUN_DIR": "/contrib/Alvaro.Vidal/tmp",
        "WORKER_LOGDIR_ROOT": "/contrib/Alvaro.Vidal/tmp",
        "SSH_CHANNEL_SCRIPT_DIR": "/contrib/Alvaro.Vidal/tmp",
        "CORES_PER_WORKER": 4
    }
}
```

The workflow runs two parsl python_app decorated functions that return the hostname:
```
Hello python_app_1 from mgmt-alvarovidal-gcpclustergen2-00028
Hello python_app_2 from alvarovidal-gcpcluster-00244-controller
```


## TODO:
Include staging test!
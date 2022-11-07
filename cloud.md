# MDLite cloud cluster instructions

These instructions detail the steps necessary for running MDLite
on a cloud cluster.  They are specific to the `main_cloud_cluster.ipynb`.

1. Configure and start a PW cloud cluster.  This cluster can have
very small nodes as the computational needs of MDLite are very 
modest. This step takes about **5 minutes**.

2. Log into the cluster (e.g. `ssh my.clusters.pw`), copy the
code to the cluster, and build a Conda environment. The default
location and name for this envionment are `$HOME/pw/miniconda`
and `mdlite`, respectively.  If you adjust these parameters,
you will need to change the corresponding values in 
`main_cloud_cluster.ipynb` so it runs in the steps below.
```bash
git clone https://github.com/parallelworks/mdlite-workflow
cd mdlite-workflow/utils
./build_conda_env.sh
```
This step takes about **5 minutes**.

3. Log out and launch a JupyterHub interactive session.  For 
example, you can use a PW GitHub workflow with the following 
`github.json` definition:
```bash
{
    "repo": "https://github.com/parallelworks/interactive_session.git",
    "branch": "main",
    "dir": ".",
    "xml": "workflow/xmls/jupyter-host/cloud.xml",
    "thumbnail": "workflow/thumbnails/jupyter.png",
    "readme": "workflow/readmes/jupyter-host/cloud.md",
    "sparsecheckout": ["jupyter-host", "utils", "controller", "partition", "platforms", "main.sh", "lib.sh", "service.html.template", "stream.sh"]
}
```
When launching the workflow, please ensure the following fields
are set to match the running cluster:
+ The currently running cluster is selected for this workflow 
with the cloud icon in the lower right corner of the launch form.
+ The `Path to Conda environment` field is set to `/home/__USER__/pw/miniconda/etc/profile.d/conda.sh`. 
(The default is `contrib` instead of `home`!)
+ The `Conda environment` is set to `mdlite` (see Step 2).
+ We are running on a `Controller` node (the head node).
This step takes about **2 minutes**.

4. Enter the JupyterHub interactive session (use the password 
defined in step 3, if defined) and navigate to and open 
`/home/<user>/mdlite-workflow/main_cloud_cluster.ipynb`. Run the 
first 9 cells for the demo.  The 10th cell will clean up 
**EVERYTHING** (except for the Conda env), including deleting 
the results!

5. Click on the `mdlite_dex.html` file as viewed in the PW IDE 
file browser to display the Design Explorer results.
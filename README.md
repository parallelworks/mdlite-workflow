# MDLITE: A lightweight Molecular Dynamics demonstration

MDLite is a small, portable molecular dynamics parameter sweep workflow
with no dependencies other than Parsl, ImageMagick, and the executables
distributed with the workflow. (Furthermore, ImageMagick is only required
on the host, the computer that initiates the workflow, not on the remote
workers.) Since the PW platform can automatically copy Parsl to remote
workers, these minimal dependencies allow this workflow to run on any
resource.  The parameter sweep outputs are visualized in the Design
Explorer. The entire workflow is embedded in a Jupyter notebook with
substantial supporting documentation; this workflow is an ideal
starting point for new users and a possible template for building
custom workflows.

The workflow is orchestrated with the
[Parsl parallel scripting library](https://parsl-project.org/) via
a Jupyter notebook ![according to this schematic](images/mdlite-parameter-sweep.png, "MDLight workflow schematic").

## Installation

This workflow can be added to your PW account from the PW marketplace
(globe icon in upper right corner).  It is also possible to install this
workflow directly from its [GitHub repository](https://github.com/parallelworks/mdlite-workflow)
with the following steps:

1. Create a new workflow by navigating to the `Workflows` tab and `Add Workflow` (select a `Parsl Notebook` workflow).
2. A new directory `/pw/workflows/<new_workflow_name>` is created.  Delete all the files that are prepopulated in this directory.
3. In the now empty PW workflow directory (do not forget the .):
```bash
git clone https://github.com/parallelworks/gromacs_solvate_membrane .
```

## Optional installation tips

By default, the PW platform will install Parsl on a remote resource
(either a cloud worker or on-premise cluster worker).  This can add
a minute or more to the workflow start, so it can be bypassed by
preinstalling Parsl on cloud worker images or on an on-premise
cluster.

### Preinstalling Parsl on an on-premise cluster

To pre-install your `.miniconda3` onto Greene; I used `/scratch/sfg3866/pworks`
and the script update_conda_path.sh is a template for updating the Conda paths
when you copy `/pw/.packs/miniconda3.tgz` manually to Greene. If you don't have
`/pw/.packs/miniconda3.tgz`, ensure `/pw/.packs` already exists
(e.g. `mkdir -p /pw/.packs`) and run `pwpack` (takes a few minutes).

The resource's settings under the PW platform Workflow tab need to be:
Work Dir: /scratch/sfg3866/pworks

### Preinstalling Parsl on a cloud worker

The `worker-ocean-parcels-13` image already has a `.miniconda3` directory
loaded in `/var/lib/pworks`.  The PW platform knows to look in that location
for an existing `.miniconda3`.

## Running the workflow

Users can run this workflow from either the workflow form or directly from
the Jupyter notebook.

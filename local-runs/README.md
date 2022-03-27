# local-runs

This directory is a space to test running the
apps in this workflow locally. The subdirectories
here (step_??) contain sample input and output
for each step along with `run.sh` scripts that
were used to verify the run command for each
app.

The SWIFT script `main.swift` is the basis
for this workflow; this repository was basically
set up to convert the SWIFT script to a Jupyter
notebook using Parsl as the workflow fabric.

**Worker image dependency warning:** Steps 3 and 4
assume that ImageMagick (convert) in installed on
the worker.  On a SLURM cluster, it may be necessary
to:
```bash
module load imagemagick/intel/7.0.10
```
(or similar) to get access to imagemagick.

## Step 1: prepInputs

The PW form will condense its input into a single text file that is stored as `params.run`.
This happens upon execution of the form.  An example of this file, with the default
inputs for the MDLite workflow, is provided in this folder.

A direct invocation of the MEXDEX function prepinputs looks like:
```bash
python ../models/mexdex/prepinputs.py params.run out.tmp
```
The resulting file, in this case `out.tmp`, is a list of all the combinations of
the different cases to run that have been set by the ranges and steps provided
in the form.

This is not a very compute intensive app; it's not essential that this app
be sent to a cloud worker - it can run locally in the workflow.

## Step 2: runMD

This is the core simulation app in the workflow. The necessary input
is a string, **one** line from the output of Step 1.  For example, a
direct run on the command line looks like:
```bash
../models/mdlite/runMD.sh "mass,0.01|npart,25|steps,3000|trsnaps,10" trajout.tmp metricout.tmp
```

## Step 3: renderFrame

This step renders the output images based on the particle trajectories
calculated in Step 2. As far as I can tell, I think there is an error
in `main.swift`: @metricOut should be in the input to renderframe
(which contains actual particle positions and more data), and not
@trjOut (which seems to contain only run summary information). An
example invocation is:
```bash
renderframe metricout.tmp out.png 1
```
Inside renderframe, the c-ray binary executable expects two pieces of
information (in text piped in via stdin):
1. a list of particle positions for that frame (from metricout.tmp) and
2. a render configuration (domain size, camera position, etc.).

## Step 4: Compile the frames into a movie

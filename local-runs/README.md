# local-runs

This directory is a space to test running the
apps in this workflow locally. The subdirectories
here (step_??) contain sample input and output
for each step along with `run.sh` scripts that
were used to verify the run command for each
app.

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
calculated in Step 2.

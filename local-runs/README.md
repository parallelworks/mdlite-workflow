# local-runs

This directory is a space to test running the
apps in this workflow locally.

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

## Step 2: runMD

## Step 3:

#!/usr/bin/env python
# coding: utf-8

import os
from os.path import exists

# Start assuming workflow is launched from the form.
run_in_notebook=False

if (exists("./resources/input_form_resource_wrapper.log")):
    print("Running from a PW form.")

    # The workflow should get inputs from the form, below.
    # The proper solution will be to grab the parameter sweep inputs
    # (a special class of inputs?) and combine them into this
    # special format.
    #
    # For now, just write a params.run:
    params="npart;input;25:50:25|steps;input;3000:6000:3000|mass;input;0.01:0.02:0.01|trsnaps;input;5:10:5|"
    print(params)
   
    # Write to params.run
    with open("params.run","w") as f:
        n_char_written = f.write(params+"\n")
    
else:
    print("Running from a notebook.")
    
    # Set flag for later
    run_in_notebook=True
    
    # Manually set workflow inputs here (same as the
    # default values in workflow launch form)
    # The ranges of EACH dimension in the parameter
    # sweep are defined by the format:
    #
    # NAME;input;MIN:MAX:STEP
    #
    #=========================================
    # npart = number of particles
    # steps = time steps in simulation
    # mass = mass of partiles
    # trsnaps = number of frames ("snapshots") of simulation for animation
    #=========================================
    params="npart;input;25:50:25|steps;input;3000:6000:3000|mass;input;0.01:0.02:0.01|trsnaps;input;5:10:5|"
    
    print(params)
    
    # Write to params.run
    with open("params.run","w") as f:
        n_char_written = f.write(params+"\n")
        
    # Run the setup stages for parsl_utils
    get_ipython().system('time ./workflow_notebook_setup.sh')


# ## Step 2: Configure Parsl
# The molecular dynamics software itself is a lightweight, precompiled executable written in C. The executable is distributed with this workflow in `./models/mdlite`, and along with input files, it is staged to the remote resources and does not need to be preinstalled.
# 
# The core visualization tool used here is a precompiled binary of [c-ray](https://github.com/vkoskiv/c-ray) distributed with this workflow in `./models/c-ray`. The executable is staged to remote resources and does not need to be preinstalled.
# 
# In addition to a Miniconda environment containing Parsl, the only other dependency of this workflow is ImageMagick's `convert` tool for image format conversion (`.ppm` to `.png`) and building animated `.gif` files from `.png` frames.

# In[ ]:


# Parsl essentials
import parsl

# PW essentials
import parsl_utils
from parsl_utils.config import config, exec_conf
from parsl_utils.data_provider import PWFile

# For embedding Design Explorer results in notebook
from IPython.display import display, HTML

# Gather inputs from the WORKFLOW FORM
import argparse
if (not run_in_notebook):
    
    # For reading command line arguments
    def read_args():
        parser=argparse.ArgumentParser()
        parsed, unknown = parser.parse_known_args()
        for arg in unknown:
            if arg.startswith(("-", "--")):
                parser.add_argument(arg)
        pwargs=vars(parser.parse_args())
        print(pwargs)
        return pwargs

    # Get any command line arguments
    args = read_args()
    job_number = args['job_number']

    print(args)
    print(job_number)

print("Configuring Parsl...")
parsl.load(config)
print("Parsl config loaded.")


# ## Step 3: Define Parsl workflow apps
# These apps are decorated with Parsl's `@bash_app` and as such are executed in parallel on the compute resources that are defined in the PW configuration loaded above.  Functions that are **not** decorated are not executed in parallel on remote resources. The files that need to be staged to remote resources will be marked with Parsl's `File()` (or its PW extension, `Path()`) in the workflow.

# In[ ]:


print("Defining Parsl workflow apps...")

from parsl.app.app import python_app, bash_app
import parsl_utils

#===================================
# Molecular dynamics simulation app
#===================================
# Sleeps inserted to allow time for
# concurrent rsyncs from all invocations
# of this app to finish transfering srcdir.
@parsl_utils.parsl_wrappers.log_app
@bash_app(executors=['cluster1'])
def md_run(case_definition, inputs=[], outputs=[], stdout='md.run.stdout', stderr='md.run.stderr'):
    return '''
    sleep 10
    mkdir -p {outdir}
    cd {outdir}
    {srcdir}/mdlite/runMD.sh "{runopt}" metric.out trj.out
    '''.format(
        runopt = case_definition,
        srcdir = inputs[0].local_path,
        outdir = outputs[0].local_path
    )

#===================================
# App to render frames for animation
#===================================
# All frames for a given simulation
# are rendered together.

# This app takes a very simple 
# approach to zero padding by adding 
# integers to 1000.
@parsl_utils.parsl_wrappers.log_app
@bash_app(executors=['cluster2'])
def md_vis(num_frames, inputs=[], outputs=[], stdout='md.vis.stdout', stderr='md.vis.stderr'):
    return '''
    sleep 10
    mkdir -p {outdir}
    for (( ff=0; ff<{nf}; ff++ ))
    do
        frame_num_padded=$((1000+$ff))
        {srcdir}/c-ray/renderframe_shared_fs {indir}/md/trj.out {outdir}/f_$frame_num_padded.ppm $ff
    done
    '''.format(
        nf = num_frames,
        srcdir = inputs[0].local_path,
        indir = inputs[1].local_path,
        outdir = outputs[0].local_path
    )

print("Done defining Parsl workflow apps.")


# ## Step 4: Workflow
# These cells execute the workflow itself.
# 
# ### Molecular dynamics simulation stage

# In[ ]:


print("Running workflow...")

#============================================================================
# SETUP PARAMETER SWEEP
#============================================================================
# Generate a case list from params.run (the ranges to parameters to sweep)
os.system("python ./models/mexdex/prepinputs.py params.run cases.list")

# Each line in cases.list is a unique combination of the parameters to sweep.
with open("cases.list","r") as f:
    cases_list = f.readlines()

#============================================================================
# SIMULATE
#============================================================================
# For each line in cases.list, run and visualize a molecular dynamics simulation
# The empty list will store the futures of Parsl-parallelized apps. Set the local
# and remote working directories for this app here.
md_run_fut = []
local_dir = os.getcwd()
remote_dir = exec_conf["cluster1"]['RUN_DIR']

for ii, case in enumerate(cases_list):
    # Define remote working (sub)dir for this case
    case_dir = "case_"+str(ii)
    
    # Run simulation
    md_run_fut.append(
        md_run(
            case_definition = case,
            inputs = [
                PWFile(
                    # Rsync with "copy dir by name" no trailing slash convention
                    url = 'file://usercontainer/'+local_dir+'/models/mdlite',
                    local_path = remote_dir+'/src'
                )
            ],
            outputs = [
                PWFile(
                    url = 'file://usercontainer/'+local_dir+'/results/'+case_dir,
                    local_path = remote_dir+'/'+case_dir+'/md'
                )
            ],
            # Any files in outputs directory at end of app are rsynced back
            stdout = remote_dir+'/'+case_dir+'/md/std.out',
            stderr = remote_dir+'/'+case_dir+'/md/std.err'
        )
    )


# ### Examples for interacting with running Parsl jobs

# In[ ]:


#md_run_fut[15].__dict__


# In[ ]:


#md_run_fut[15].task_def


# In[ ]:


#config.executors[0].provider.cancel(["0","2","15"])


# ### Force workflow to wait for all simulation apps

# In[ ]:


# Call results for all app futures to require
# execution to wait for all simulations to complete.
for run in md_run_fut:
    run.result()
    
print('Done with simulations.')


# ### Visualization stage

# In[ ]:


#============================================================================
# VISUALIZE
#============================================================================
md_vis_fut = []
local_dir = os.getcwd()
remote_dir = exec_conf["cluster2"]['RUN_DIR']

for ii, case in enumerate(cases_list):
    # Define remote working dir for this case
    case_dir = "case_"+str(ii)
        
    # Get number of frames to render for this case
    nframe = int(case.split(',')[4])
    
    #=========================================================
    # Render all frames for each case in one app.  This approach
    # reduces the number of SSH connections (e.g. rsync instances) 
    # compared to an app that only renders one frame at a time.
    md_vis_fut.append(
        md_vis(
            nframe,
            inputs=[
                PWFile(
                    url = 'file://usercontainer/'+local_dir+'/models/c-ray',
                    local_path = remote_dir+'/src'
                ),
                PWFile(
                    url = 'file://usercontainer/'+local_dir+'/results/'+case_dir+'/md',
                    local_path = remote_dir+'/'+case_dir
                )
            ],
            outputs=[
                PWFile(
                    url = 'file://usercontainer/'+local_dir+'/results/'+case_dir,
                    local_path = remote_dir+'/'+case_dir+'/vis'
                )
            ],
            stdout = remote_dir+'/'+case_dir+'/vis/std.out',
            stderr = remote_dir+'/'+case_dir+'/vis/std.err'
        )
    )

for vis in md_vis_fut:
    vis.result()
    
# Compile frames into movies locally
for ii, case in enumerate(cases_list):
    os.system("cd ./results/case_"+str(ii)+"/vis; convert -delay 10 *.ppm mdlite.gif")

# Compile movies into Design Explorer results locally
os.system("./models/mexdex/postprocess.sh mdlite_dex.csv mdlite_dex.html ./")

print('Done with visualizations.')


# ## Step 5: View results
# This step is only necessary when running directly in a notebook. The outputs of this workflow are stored in the `results` folder and they can be interactively visualized with the Design Explorer by clicking on `mdlite_dex.html` which uses `mdlite_dex.csv` and the data in the `results` folder. The Design Explorer visualization is automatically embedded below.

# In[ ]:


# Modify width and height to display as wanted
from IPython.display import IFrame
def designExplorer(url,height=600):
    return IFrame(url, width=800, height=height)

# Make sure path to datafile=/pw/workflows/mdlite/mdlite_dex.csv is correct
nb_cwd = os.getcwd()
designExplorer(
    '/DesignExplorer/index.html?datafile='+nb_cwd+'/mdlite_dex.csv&colorby=kinetic',
    height=600)


# ## Step 6: Use notebook to interact directly with simulation results
# Jupyter notebooks are great because cells can be re-run in isolation as ideas are fine-tuned.  The cell below allows for plotting a new result directly from the simulation outputs; there is no need to re-run the simulation if the plot needs to be modified as the user explores the results.

# In[ ]:


# Import needed libraries
import pandas as pd
import numpy as np
import glob
import math 
import matplotlib.pyplot as plt


# ### Load data and compute statistics

# In[ ]:


# All data are in the results/case_* folders.
list_of_cases = glob.glob("results/case_*")

# Initialize lists to store data for plotting
cases = []
all_cases_time_val = []
all_cases_rt_mean_sq_std = []
all_cases_rt_mean_sq_mean = []

# Loop through each case
for case in list_of_cases:

    # Get info about this case
    path = case + "/md/trj.out"
    case_name = case[case.index('case'):]
    cases.append(case_name)
    
    # Load data for this case
    data = pd.read_csv(path, sep=" ")
    data.columns=['time', 'var', 'x_pos', 'y_pos', 'z_pos', 'ig0', 'ig1', 'ig2', 'ig3', 'ig4', 'ig5']
    t_val = data['time'].unique()
    all_cases_time_val.append(t_val)
    
    # Create and initialize lists of root mean square for std and mean
    one_case_rt_mean_sq_std = []
    one_case_rt_mean_sq_mean = []

    # Loop through each instance in time and compute statistics
    for t in t_val:

        each_time = data.loc[data['time'] == t, 'x_pos':'z_pos']
        all_pos_std = each_time.std()
        all_pos_mean = each_time.mean()
        
        # Calculate root mean square of std and mean (vector magnitude)
        # Fix decimal points to 6
        rt_mean_sq_std = math.sqrt((all_pos_std['x_pos'])**2 + (all_pos_std['y_pos'])**2 + (all_pos_std['z_pos'])**2)
        one_case_rt_mean_sq_std.append(round(rt_mean_sq_std,6))
        rt_mean_sq_mean = math.sqrt((all_pos_mean['x_pos'])**2 + (all_pos_mean['y_pos'])**2 + (all_pos_mean['z_pos'])**2)
        one_case_rt_mean_sq_mean.append(round(rt_mean_sq_mean,6))
        
    # After getting all root mean square for std and mean of all time,
    # put it in the list for all cases.
    all_cases_rt_mean_sq_std.append(one_case_rt_mean_sq_std)
    all_cases_rt_mean_sq_mean.append(one_case_rt_mean_sq_mean)


# ### Plot

# In[ ]:


# Plot side by side root mean square std vs. time 
# and root mean square mean vs. time
fig, (ax0, ax1) = plt.subplots(1,2,figsize=(20,5))

# Go through each cases to plot
# If desired to see some case not all,
# could change range(len(cases)) to range(<some number less than len(cases)>)
for c in range(len(cases)):
    # Plot root mean square std vs. time with solid line
    # and dots for each value (x,y) on the graph
    # x-axis is time, y-axis is root mean square std
    ax0.plot(all_cases_time_val[c],all_cases_rt_mean_sq_std[c],'-o')
    ax0.set_xlabel('Time(s)', fontsize=20)
    ax0.set_ylabel('RMS variance of positions', fontsize=15)

    # Plot root mean square mean vs. time with solid line
    # and squares for each value (x,y) on the graph
    # x-axis is time, y-axis is root mean square mean
    ax1.plot(all_cases_time_val[c],all_cases_rt_mean_sq_mean[c],'-s')
    ax1.set_xlabel('Time(s)', fontsize=20)
    ax1.set_ylabel('Magnitude of centroid position', fontsize=15)
    
# Add legend to show name of each case
ax0.legend(cases)
ax1.legend(cases)

# Add title for each plot
ax0.set_title("Spread of particle swarm",
              fontsize=25)
ax1.set_title("Centroid of particle swarm",
              fontsize=25)


# ## Step 7: Clean up
# This step is only necessary when running directly in a notebook. These intermediate and log files are removed to keep the workflow file structure clean if this workflow is pushed into the PW Market Place.  Please feel free to comment out these lines in order to inspect intermediate files as needed. The first two, `params.run` and `cases.list` are explicitly created by the workflow in Steps 1 and 4, respectively.  The other files are generated automatically for logging, keeping track of workers, or starting up workers. **Note that even the results are deleted!**

# In[ ]:


if (run_in_notebook):
    # Shut down Parsl
    parsl.dfk().cleanup()
    
    # Shut down tunnels
    get_ipython().system('time ./kill.sh')
    
    # Destroy workdirs on remote clusters
    # .clusters.pw ONLY WORKS FOR CLOUD CLUSTERS!
    cname = exec_conf["cluster1"]["POOL"]
    workd = exec_conf["cluster1"]['RUN_DIR']
    get_ipython().system('ssh {cname}.clusters.pw rm -rf {workd}')
    
    cname = exec_conf["cluster2"]["POOL"]
    workd = exec_conf["cluster2"]['RUN_DIR']
    get_ipython().system('ssh {cname}.clusters.pw rm -rf {workd}')
    
    # Delete intermediate files/logs that are NOT core code or results
    get_ipython().system('rm -f params.run')
    get_ipython().system('rm -f cases.list')
    get_ipython().system('rm -rf runinfo')
    get_ipython().system('rm -rf __pycache__')
    get_ipython().system('rm -rf logs')
    get_ipython().system('rm -rf cluster1')
    get_ipython().system('rm -rf cluster2')
    get_ipython().system('rm -f exec_conf*')
    get_ipython().system('rm -f executors*.json')
    get_ipython().system('rm -f kill.sh')
    get_ipython().system('rm -f local.conf')
    get_ipython().system('rm -f pw.conf')
    get_ipython().system('rm -f vars')
    get_ipython().system('rm -f service.html')
    
    # Delete supporting code (cloned in workflow_notebook_setup.sh)
    get_ipython().system('rm -rf parsl_utils')
    
    # Delete outputs
    get_ipython().system('rm -rf ./results')
    get_ipython().system('rm -f mdlite_dex.*')


# In[ ]:





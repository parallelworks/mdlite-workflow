#======================================================
# MDLite - Lightweight Molecular Dynamics demo workflow
#======================================================

# The molecular dynamics software itself is a lightweight,
# precompiled executable written in C. The executable is
# distributed with this workflow in `./models/mdlite`, and
# along with input files, it is staged to the remote resources
# and does not need to be preinstalled.
# 
# The core visualization tool used here is a precompiled
# binary of [c-ray](https://github.com/vkoskiv/c-ray) distributed
# with this workflow in `./models/c-ray`. The executable is
# staged to remote resources and does not need to be preinstalled.
#
# In addition to a Miniconda environment containing Parsl, the
# only other dependency of this workflow is ImageMagick's
# `convert` tool for image format conversion (`.ppm` to
# `.png`) and building animated `.gif` files from `.png` frames.
#
# This workflow is set up to run the similations on one
# cluster and the visualization on another cluster to demonstrate
# multi-site workflow functionality. If you specify the same
# cluster for both tasks, it can run the whole workflow on
# a single cluster.

#======================================================
# Dependencies
#======================================================

# Basic dependencies
import os
from os.path import exists

# Parsl essentials
import parsl
from parsl.app.app import python_app, bash_app
print(parsl.__version__, flush = True)

# PW essentials
import parsl_utils
from parsl_utils.config import config, resource_labels, form_inputs
from parsl_utils.data_provider import PWFile

# For embedding Design Explorer results in notebook
from IPython.display import display, HTML

# For making a plot of the results
import pandas as pd
import numpy as np
import glob
import math
import matplotlib.pyplot as plt

#==================================================
# Step 1: Inputs
#==================================================

# Start assuming workflow is launched from the form.

# Gather inputs from the WORKFLOW FORM    
# The form_inputs, resource_labels, and
# Parsl config built by parsl_utils are
# all loaded above with the import statement.
# Each of these three data structures
# has different information:
# 1. resource_labels is a simple list of the 
#    resource names specified in the workflow
#    which are used for accessing more details
#    about each resource in the form_inputs or
#    Parsl config.
# 2. form_inputs is a record of the user selected
#    parameters of the workflow from the 
#    workflow.xml workflow launch form.  Additional
#    information is added by the PW platform. 
#    Some form information is *hidden* in the
#    workflow.xml and not visible to the user in
#    the GUI, but it can be modified by editing
#    the workflow.xml. This approach provides a
#    way to differentiate between commonly changed
#    parameters and parameters that rarely change.
# 3. the Parsl config is build by the PW platform
#    (specifically the parsl_utils wrapper used to
#    launch this workflow querying info from the
#    PW databases via the PW API). Some of this
#    information is duplicated in the form_inputs,
#    but it is in a special format needed by Parsl.
#
# Print out each of these data structures to see
# exactly what is contained in each.

print('--------------RESOURCE-LABELS---------------')
print(resource_labels)
print('----------------FORM-INPUTS-----------------')
print(form_inputs)
print('----------------PARSL-CONFIG----------------')
print(config)

# The main "scientific" workflow parameters (as opposed
# to all the params necessary to specify compute 
# resources, etc.) are in the geometry section of the
# form_inputs. To use the DesignExplorer infrastructure
# for a parameter sweep, these parameters are assembled 
# together into a single file, params.run, which will
# be used to build up the mix-and-match case list.

# Initialize an empty string to append to.
params_run_str = ''

# Loop over each parameter in the geometry section.
for param in form_inputs['geometry']:
    print(param)
    params_run_str = params_run_str+param+";input;"+form_inputs['geometry'][param]+"|"

print(params_run_str)
# Write to params.run
with open("params.run","w") as f:
    n_char_written = f.write(params_run_str+"\n")

run_in_notebook = form_inputs['run_in_notebook']
print(run_in_notebook)
if (run_in_notebook == "True" ):
    print('Detected request to run in notebook. Blocking execution in main.py.')
    print('Please open '+os.pwd+'/main.ipynb to continue.')
    # If the user clicks on the "Run in Jupyter notebook"
    # toggle switch, skip the workflow code here (the user
    # will run it in the notebook) and wait for the user
    # to execute the finish cell of the notebook. 
    iii = 0
    while iii < 1:
        if (exists("notebook_done.flag")): iii = 1
        sleep(30)
else:
    print("Running workflow directly in main.py...")
    
    #==================================================
    # Step 2: Configure Parsl
    #==================================================
    
    print("Loading Parsl config...")
    parsl.load(config)
    print("Parsl config loaded.")
    
    #==================================================
    # Step 3: Define Parsl workflow apps
    #==================================================
    
    # These apps are decorated with Parsl's `@bash_app` 
    # and as such are executed in parallel on the compute 
    # resources that are defined in the Parsl config 
    # loaded above.  Functions that are **not** decorated 
    # are not executed in parallel on remote resources. 
    #
    # The files that need to be staged to remote resources 
    # will be marked with Parsl's `File()` (or its PW 
    # extension, `PWFile()`) in the workflow.
    
    print("Defining Parsl workflow apps...")
    
    #===================================
    # Molecular dynamics simulation app
    #===================================
    # Sleeps inserted to allow time for
    # concurrent rsyncs from all invocations
    # of this app to finish transfering srcdir.
    
    # This decorator will print out the inputs and
    # outputs (full local path, i.e. path where the
    # parsl script is running) but is not strictly
    # necessary for running the workflow.
    #@parsl_utils.parsl_wrappers.log_app
    @bash_app(executors=[resource_labels[0]])
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
    #@parsl_utils.parsl_wrappers.log_app
    @bash_app(executors=[resource_labels[1]])
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
    
    #==================================================
    # Step 4: Workflow
    #==================================================
    
    # These cells execute the workflow itself.
    # First, we have the molecular dynamics simulation.
    
    print("Running simulation...")
    
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
    remote_dir = config.executors[0].working_dir+"/sim"
    
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
    
    
    # Force workflow to wait for all simulation apps
    # Call results for all app futures to require
    # execution to wait for all simulations to complete.
    for run in md_run_fut:
        run.result()
        
    print('Done with simulations.')
    
    #============================================================================
    # VISUALIZE
    #============================================================================
    md_vis_fut = []
    local_dir = os.getcwd()
    remote_dir = config.executors[1].working_dir+"/vis"
    
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

    #============================================================================
    # Use notebook to interact directly with simulation results
    #============================================================================
    # Jupyter notebooks are great because cells can be re-run in isolation as ideas are fine-tuned.  The cell below allows for plotting a new result directly from the simulation outputs; there is no need to re-run the simulation if the plot needs to be modified as the user explores the results.

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
    ax0.set_title("Spread of particle swarm",fontsize=25)
    ax1.set_title("Centroid of particle swarm",fontsize=25)
    plt.savefig("mdlite_results.png")


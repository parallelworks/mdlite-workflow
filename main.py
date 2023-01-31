import sys, os, json, time
from os.path import exists
from random import randint

import parsl
print(parsl.__version__, flush = True)
from parsl.app.app import python_app, bash_app

import parsl_utils
from parsl_utils.config import config, exec_conf, pwargs, job_number
from parsl_utils.data_provider import PWFile

from workflow_apps import *


# Job runs in directory /pw/jobs/job-number
job_number = os.path.dirname(os.getcwd().replace('/pw/jobs/', ''))

if __name__ == '__main__':

    print('Loading Parsl Config', flush = True)
    parsl.load(config)

    if (exists("./params.run")):
        print("Running from a PW form.")

    else:
        print("Running from a local dir.")

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

    os.system("python ./models/mexdex/prepinputs.py params.run cases.list")

    # Each line in cases.list is a unique combination of the parameters to sweep.
    with open("cases.list","r") as f:
        cases_list = f.readlines()

    #============================================================================
    # SIMULATE
    #============================================================================
    # For each line in cases.list, run and visualize a molecular dynamics simulation
    # These empty lists will store the futures of Parsl-parallelized apps.
    # Use Path for staging because multiple files in ./models/mdlite are needed
    # and mutliple files in ./results/case_*/md are sent back to the platform.
    md_run_fut = []
    for ii, case in enumerate(cases_list):
        fut_1 = md_run(
            rundir = exec_conf[EXECUTOR]['RUN_DIR'] + '/' + str(ii),
            case = case,
            inputs = [
                PWFile(
                    url = 'file://usercontainer/{cwd}/models/mdlite/*'.format(cwd = os.getcwd()),
                    local_path = '{remote_dir}'.format(remote_dir = exec_conf[EXECUTOR]['RUN_DIR'] + '/' + str(ii))
                )
            ],
            outputs = [
                PWFile(
                    url = 'file://usercontainer/{cwd}/results/case_'.format(cwd = os.getcwd()) +str(ii) + '/mdlite',
                    local_path = '{remote_dir}/mdlite/'.format(remote_dir =  exec_conf[EXECUTOR]['RUN_DIR'] + '/' + str(ii))
                )
            ],
            stdout = os.path.join(exec_conf[EXECUTOR]['RUN_DIR'] + '/' + str(ii), 'std.out'),
            stderr = os.path.join(exec_conf[EXECUTOR]['RUN_DIR'] + '/' + str(ii), 'std.err')
        )

        md_run_fut.append(fut_1)

    #============================================================================
    # VISUALIZE
    #============================================================================
    md_vis_fut = []
    for ii, case in enumerate(cases_list):
        # Get number of frames to render for this case
        nframe = int(case.split(',')[4])

        fut_2 = md_vis(
            rundir = exec_conf[EXECUTOR]['RUN_DIR'] + '/' + str(ii),
            nframe=nframe,
            inputs = [
                PWFile(
                    url = 'file://usercontainer/{cwd}/models/c-ray/*'.format(cwd = os.getcwd()),
                    local_path = '{remote_dir}'.format(remote_dir =  exec_conf[EXECUTOR]['RUN_DIR'] + '/' + str(ii))
                ),
                PWFile(
                    url = 'file://usercontainer/{cwd}/results/case_'.format(cwd = os.getcwd()) + str(ii) + '/mdlite/',
                    local_path = '{remote_dir}/mdlite'.format(remote_dir = exec_conf[EXECUTOR]['RUN_DIR'] + '/' + str(ii))
                ),
                *md_run_fut
            ],
            outputs = [
                PWFile(
                    url = 'file://{cwd}/results/case_'.format(cwd = os.getcwd()) + str(ii) + '/viz',
                    local_path = '{remote_dir}/viz/'.format(remote_dir =  exec_conf[EXECUTOR]['RUN_DIR'] + '/' + str(ii))
                )
            ],
            stdout = os.path.join(exec_conf[EXECUTOR]['RUN_DIR'] + '/' + str(ii), 'std.out'),
            stderr = os.path.join(exec_conf[EXECUTOR]['RUN_DIR'] + '/' + str(ii), 'std.err')
        )

        md_vis_fut.append(fut_2)

    for vis in md_vis_fut:
        vis.result()

    print("Tasks completed - compiling frames into animations...")

    # Compile frames into movies locally
    for ii, case in enumerate(cases_list):
        os.system("cd ./results/case_"+str(ii)+"/viz; convert -delay 10 *.ppm mdlite.gif")

    # Compile movies into Design Explorer results locally
    os.system("./models/mexdex/postprocess.sh mdlite_dex.csv mdlite_dex.html ./")
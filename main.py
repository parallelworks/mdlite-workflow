import sys, os, json, time
from os.path import exists
from random import randint

import parsl
print(parsl.__version__, flush = True)
from parsl.app.app import python_app, bash_app

from config import config,exec_conf,read_args

import parsl_utils

# Job runs in directory /pw/jobs/job-number
job_number = os.path.dirname(os.getcwd().replace('/pw/jobs/', ''))

# PARSL APPS:
@parsl_utils.parsl_wrappers.log_app
@python_app(executors=['myexecutor_1'])
def hello_python_app_1(name = '', stdout='std.out', stderr = 'std.err'):
    import socket
    if not name:
        name = 'python_app_1'
    return 'Hello ' + name + ' from ' + socket.gethostname()

@parsl_utils.parsl_wrappers.log_app
@parsl_utils.parsl_wrappers.stage_app(exec_conf['myexecutor_1']['HOST_USER'] + '@' + exec_conf['myexecutor_1']['HOST_IP'])
@bash_app(executors=['myexecutor_1'])
def md_run(rundir, case, inputs_dict = {}, outputs_dict = {}, stdout='md.run.stdout', stderr='md.run.stderr'):
    return '''
    echo running mdlite in $rundir
    mkdir -p {rundir} && cd {rundir}
    chmod +x runMD.sh
    mkdir -p {outdir} && cd {outdir}
    ../runMD.sh "{case}" metric.out trj.out
    '''.format(
        rundir=rundir,
        case=case,
        outdir=outputs_dict['results']['worker_path']
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
@parsl_utils.parsl_wrappers.stage_app(exec_conf['myexecutor_1']['HOST_USER'] + '@' + exec_conf['myexecutor_1']['HOST_IP'])
@bash_app(executors=['myexecutor_1'])
def md_vis(rundir, nframe, inputs_dict={}, outputs_dict={}, stdout='md.vis.stdout', stderr='md.vis.stderr'):
    return '''
    echo running {nframe} c-ray in {rundir}
    mkdir -p {rundir} && cd {rundir}
    indir="{indir}"
    outdir="{outdir}"
    rm -f $outdir && mkdir -p $outdir
    chmod +x *
    for (( ff=0; ff<{nframe}; ff++ ))
    do
        frame_num_padded=$((1000+$ff))
        ./renderframe_shared_fs $indir/trj.out $outdir/f_$frame_num_padded.ppm $ff
    done
    '''.format(
        rundir=rundir,
        nframe=nframe,
        indir=inputs_dict['md-results']['worker_path'],
        outdir=outputs_dict['results']['worker_path']
    )

if __name__ == '__main__':
    args = read_args()
    job_number = args['job_number']

    print('Loading Parsl Config', flush = True)
    parsl.load(config)

    # print('\n\n\nHELLO PYTHON APP:', flush = True)
    # fut_1 = hello_python_app_1(name = args['name'])
    # print(fut_1.result())

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
            rundir = exec_conf['myexecutor_1']['RUN_DIR'] + '/' + str(ii),
            case=case,
            inputs_dict = {
                "model": {
                    "type": "file",
                    "global_path": "pw://{cwd}/models/mdlite/*",
                    "worker_path": "{remote_dir}".format(remote_dir =  exec_conf['myexecutor_1']['RUN_DIR'] + '/' + str(ii))
                }
            },
            outputs_dict = {
                "results": {
                    "type": "directory",
                    "global_path": "pw://{cwd}/results/case_"+str(ii)+'/mdlite',
                    "worker_path": "{remote_dir}/mdlite".format(remote_dir =  exec_conf['myexecutor_1']['RUN_DIR'] + '/' + str(ii))
                }
            },
            stdout = os.path.join(exec_conf['myexecutor_1']['RUN_DIR'] + '/' + str(ii), 'std.out'),
            stderr = os.path.join(exec_conf['myexecutor_1']['RUN_DIR'] + '/' + str(ii), 'std.err')
        )

        md_run_fut.append(fut_1)

    for run in md_run_fut:
        run.result()

    #============================================================================
    # VISUALIZE
    #============================================================================
    md_vis_fut = []
    for ii, case in enumerate(cases_list):
        # Get number of frames to render for this case
        nframe = int(case.split(',')[4])

        fut_2 = md_vis(
            rundir = exec_conf['myexecutor_1']['RUN_DIR'] + '/' + str(ii),
            nframe=nframe,
            inputs_dict = {
                "model": {
                    "type": "file",
                    "global_path": "pw://{cwd}/models/c-ray/*",
                    "worker_path": "{remote_dir}".format(remote_dir =  exec_conf['myexecutor_1']['RUN_DIR'] + '/' + str(ii))
                },
                "md-results": {
                    "type": "directory",
                    "global_path": "pw://{cwd}/results/case_"+str(ii)+"/mdlite",
                    "worker_path": "{remote_dir}/mdlite".format(remote_dir =  exec_conf['myexecutor_1']['RUN_DIR'] + '/' + str(ii))
                }
            },
            outputs_dict = {
                "results": {
                    "type": "directory",
                    "global_path": "pw://{cwd}/results/case_"+str(ii)+'/viz',
                    "worker_path": "{remote_dir}/viz".format(remote_dir =  exec_conf['myexecutor_1']['RUN_DIR'] + '/' + str(ii))
                }
            },
            stdout = os.path.join(exec_conf['myexecutor_1']['RUN_DIR'] + '/' + str(ii), 'std.out'),
            stderr = os.path.join(exec_conf['myexecutor_1']['RUN_DIR'] + '/' + str(ii), 'std.err')
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
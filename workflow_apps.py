from parsl.app.app import python_app, bash_app
import parsl_utils

EXECUTOR = 'executor'
# PARSL APPS:
@parsl_utils.parsl_wrappers.log_app
@bash_app(executors=[EXECUTOR])
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
@bash_app(executors=[EXECUTOR])
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

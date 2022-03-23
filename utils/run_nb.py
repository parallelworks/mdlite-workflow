#!/pw/.miniconda3/envs/parsl-pw/bin/python
import os
import os.path as osp
import sys
import subprocess
import json
name = osp.basename(sys.argv[0])
notebook = sys.argv[1]
script = notebook.replace('.ipynb', '.py')
if not osp.exists(script) or osp.getmtime(notebook) > osp.getmtime(script):
    subprocess.call(['jupyter', 'nbconvert', '--log-level', '0', '--to', 'script', notebook])
os.execlp('python3', script, script, *sys.argv[2:])
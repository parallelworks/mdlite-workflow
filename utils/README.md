# Helper scripts for executing/testing MDLite

## Rsync tests

`setup_rsync_tests.sh` and `run_rsync_tests.sh` are designed to test
limits to the number of concurrent rsync sessions.

Rsync test results:
usercontainer has `MaxSessions=1000` -> fails with more than 10 concurrent transfers from head node
usercontainer AND head node have `MaxSessions=1000` -> fails again

The critical parameter is to have both increased in `MaxSessions` AND `MaxStartups`
in the usercontainer.  The default values can be retained on the remote resource,
even when that resource is initiating a few hundred file transfer.

Trying 900 files (1MB each), only 865 files were able to transfer with `MaxStartups=1000:30:6000` and `MaxSessions=1000`
in the user container, so this problem is not entirely solved.  It may be that there are
issues with hundreds of concurrent rsyncs OR there are more background conections than expected. For
example, a possibility is that when you initiate hundreds of concurrent rsyncs, there is a distinct
lag between the time the individual rsync is launched and when the file arrives (or when the tmp file
arrives, too) -> there could be an SSH timeout that kills the job if it takes too long to start its
transfer while that job is waiting for the other jobs to finish.

Trying 500 files (1MB each) was successful (so maybe a 50% of MaxSessions rule of thumb applies?). I need to 
experiment with larger files, other settings for `MaxSessions` and `MaxStartups`, and SSH timeout settings.
With the default settings on the cluster head node (i.e. MaxSessions=10)and the increased limits on the usercontainer, I
was able to send 500 files to the usercontainer and 500 files from the usercontainer back to the head node.
All rsync commands were initiated on the head node, not in the user container.

## Worker versus head nodes

I think that the sshd_config needs to be adjusted on the cluster HEAD node in addition to the user container
if the new `parsl_utils` `rsync` data provider is going to be used. The reason for this is that the
SSH tunnels between the head node and the user container are being used by the worker node, e.g.
```
rsync -avzq  -e 'ssh -J <head_node_internal_ip' $file usercontainer:/pw/tmp
```
So the rsync operations are going through the head node to the usercontainer; the head node's sshd_config
is involved now, too, not just the usercontainer's. In particular, if only 9 concurrent files are sent,
then everything is OK because the default config on most head nodes (depends system-to-sytem!) is for 
10 concurrent sessions. One of the 10 sessions is taken up by the connection between the usercontainer
and the head node, that leaves 9 concurrent sessions available for rsync.

However, it is not MaxSessions and MaxStartups.  Those values are set to the default 10 limit on the
PW cloud clusters and there is no rsync file transfer issue. Instead, I think there is a requirement
to allow the SSH daemon to establish a perstent multiplex connection - and if rsync is pushing requests
during that time, things fail.  Can I insert a sleep in the -e? No, I cannot.

But, I could run a single Parsl app to rsync a single file - this would establish the
SSH multiplex connect that seems to be needed for the worker:
```
[user@WORKER_NODE]$ ps -u user -HF
UID        PID  PPID  C    SZ   RSS PSR STIME TTY          TIME CMD
user  43808 43802  0 31732  3244   9 16:56 pts/0    00:00:00 /bin/bash
user   7774 43808  0 41442  1920  16 17:04 pts/0    00:00:00   ps -u user -HF
user  47828     1  0 47500  2492   8 16:58 ?        00:00:01 ssh: /home/user/.ssh/PW_USER@localhost:2222 [mux]
user  47811     1  0 47308  4256   7 16:58 pts/0    00:00:00 ssh -W localhost:2222 10.3.14.210
user  47821 47811  0 55472  3196   8 16:58 pts/0    00:00:00   /usr/bin/sss_ssh_knownhostsproxy -p 22 10.3.14.210
```
A simple `srun -N 1 --pty /bin/bash` command onto this WORKER_NODE results in
only the top two jobs. The bottom three get established with the execution of
rsync to the usercontainer. Once they are established, files get transfered
(most of the time - there are still errors and about 1% are dropped for other
reasons? i.e. 3 files out of 400)


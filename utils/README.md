# Helper scripts for executing/testing MDLite

## Rsync tests

### Summary 

`setup_rsync_tests.sh` and `run_rsync_tests.sh` are designed to test
limits to the number of concurrent rsync sessions.

### Motivation

PWRsyncStaging is the default mechanism for staging files to/from 
whereever Parsl is running and the worker nodes.

### Description of solutions

There are two basic approaches that can be used to set up robust
concurrent `rsync` file transfers (which use `ssh` connections).
1. Use many different ssh/rsync connections.  If sending more
   than 10 files at once, this approach requires increasing
   `MaxSessions` and `MaxStartups` in `/etc/ssh/sshd_config`.
2. Option 1 incurrs additional computational cost on the nodes
   that have to deal with the additional authentication load
   of the many ssh connections. Also, Option 1 may simply not
   be possible on certain systems since `/etc/ssh/sshd_config` is
   normally not accessible to regular users. The alternative,
   general approach is to set up an ssh multiplex session between
   every individual worker node and the head node
   and all subsequent ssh/rsync connections are channeled through
   the multiplex session. This approach requires the following
   in `~/.ssh/config`:
```
ControlMaster auto
ControlPersist yes
ControlPath /home/<user>/.ssh/%r@%h:%p
```
   (the `ControlPath` is not strictly required, but it's really useful)

### Tests to verify the solutions described above

In all cases, run `./setup_rsync_test.sh` to create a data set for
testing. This script will by default create 20 100MB files. The default
limits on `MaxSessions` is 10, so attempting to send these files
at the same time with `./run_rsync_tests.sh` will usually trip the 
`MaxSessions` limit.  However, in practice, it also depends on how fast
the computers are - if they are slow (only a few CPU) then 10 jobs are
listed in `ps` but they are not actually pinging the ssh daemon fully
concurrently and so you can get more than 10 files through. For blazing
fast nodes, however, you should notice the `MaxSessions` limit immediately.

To limit `./run_rsync_test.sh` to sending exactly 10 files (to check
the `MaxSessions` limit precisely) you can insert `| head -10` in the
for loop on line 7 right after the `ls` command.

Here is a sample session for running the test in a way that
simulates the behavior of PWRsyncStaging:
```
# Get the internal IP of the cluster head node
hostname -I

# Put the internal (first) IP address of the
# head node after the `-J` in ./run_rsync_tests.sh 

# Create sample data set
./setup_rsync_tests.sh

# Get onto a worker node
srun -N 1 -n 2 --pty /bin/bash

# Run the test
./run_rsync_tests.sh
```

#### Option 1 (many ssh connections) test results:

usercontainer has `MaxSessions=1000` -> fails with 
more than 10 concurrent transfers from head node
usercontainer AND head node have `MaxSessions=1000` -> fails again

The critical parameter is to have both increased in 
`MaxSessions` AND `MaxStartups` in the usercontainer.  
The default values can be retained on the remote resource,
even when that resource is initiating a few hundred file transfer.

Trying 900 files (1MB each), only 865 files were able to 
transfer with `MaxStartups=1000:30:6000` and `MaxSessions=1000`
in the user container, so this problem is not entirely solved.
It may be that there are issues with hundreds of concurrent rsyncs 
OR there are more background conections than expected. For
example, a possibility is that when you initiate hundreds of 
concurrent rsyncs, there is a distinct lag between the time the 
individual rsync is launched and when the file arrives (or when the tmp file
arrives, too) -> there could be an SSH timeout that kills the 
job if it takes too long to start its transfer while that job 
is waiting for the other jobs to finish.

Trying 500 files (1MB each) was successful (so maybe a 50% of 
MaxSessions rule of thumb applies?). I need to  experiment with 
larger files, other settings for `MaxSessions` and `MaxStartups`, 
and SSH timeout settings.

With the default settings on the cluster head node 
(i.e. MaxSessions=10) and the increased limits on the usercontainer, 
I was able to send 500 files to the usercontainer and 500 files from 
the usercontainer back to the head node. All rsync commands were 
initiated on the head node, not in the user container. The take home
point here is that it is the `sshd_config` **whereever the ssh daemon
is running** that limits `MaxSessions`. For head node direct to
usercontainer, this means only the usercontainer `sshd_config` is
involved.  However, for worker nodes using `ssh -J` to connect
to the usercontainer through the head node, this means that there
is also an ssh daemon involved on the **head node**.

#### Option 2: ssh multiplexing

If you add `ControlMaster auto` and `ControlPersist yes` to your ssh config,
multiplexing will be enabled. The underlying issue here is that there is
a time lag for establishing the multiplex session, so if you run the test
described above on a fresh worker node, it is likely to fail because the
first time you run the test, you need to establish the multiplex connection
and there is a race condition between the first ssh/rsync request (that
starts the multiplexing) and all the other concurrent ssh/rsync requests.

However, when you run the same script a **second** time, it works because
the multiplex session was already established.  You can always check for
whether a multiplex session is active with the following:
```
# Start a session
ssh -J <head_node_internal_ip> usercontainer
exit

# Multiplex sessions are stored as sockets on the ControlPath
# for example, sfgary@localhost:2222 is a socket.
[sfgary@compute-0001 utils]$ ls ~/.ssh/
authorized_keys  config  id_rsa  id_rsa.pub  masterip  sfgary@localhost:2222  userscript

# You can check the status of a connection using the same
# notation as it was opened:
ssh -J <head_node_internal_ip> -O check usercontainer

# You can also close a multiplex session:
ssh -J <head_node_internal_ip> -O stop usercontainer

# And cross check it is closed:
[sfgary@compute-0001 utils]$ ls ~/.ssh/
authorized_keys  config  id_rsa  id_rsa.pub  masterip  userscript
```

I suspect that a faily deep integration with Parsl would be
required to automatically and always establish an ssh multiplex
connection for every worker node that Parsl calls up. Instead,
let's try:
1. including timeout and retry options for the ssh shell 
   with `-o ConnectTimeout=10 -o ConnectionAttempts=10`. This 
   may allow processes that have issues to keep trying while also
   allowing the first process to establish the multiplex connection.
   **DOES NOT WORK**
2. Let's remove the above and try rsync specific options: --timeout and --contimeout
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


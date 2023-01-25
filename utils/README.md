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


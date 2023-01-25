# Helper scripts for executing/testing MDLite

## Rsync tests

`setup_rsync_tests.sh` and `run_rsync_tests.sh` are designed to test
limits to the number of concurrent rsync sessions.

Test results:
usercontainer has `MaxSessions=1000` -> fails with more than 10 concurrent transfers from head node
usercontainer AND head node have `MaxSessions=1000` -> fails again



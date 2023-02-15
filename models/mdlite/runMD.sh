#! /bin/bash

export HOME=$PWD

caseParams=$1
metricout=$HOME/$2
trjout=$HOME/$3

# Check command line inputs
echo "======================="
echo caseParams: $caseParams
echo metricout: $metricout
echo trajout: $trjout
echo "======================"
echo " "

npart=$(echo $caseParams | tr '|' '\n' | grep npart | awk -F',' '{print $2}')
steps=$(echo $caseParams | tr '|' '\n' | grep steps | awk -F',' '{print $2}')
trsnaps=$(echo $caseParams | tr '|' '\n' | grep trsnaps | awk -F',' '{print $2}')
mass=$(echo $caseParams | tr '|' '\n' | grep mass | awk -F',' '{print $2}')

# Check parsing of caseParams
echo " "
echo "========================"
echo Number of particles: $npart
echo Simulation steps: $steps
echo Visulation snaps: $trsnaps
echo Particle mass: $mass
echo "======================="
echo " "

# Get directory with binary. Use $0, but
# %/* will match the last instance of "/"
# in $0 and remove everything after it.
bindir=${0%/*}

# Not needed since permissions are preserved.
#chmod 777 * -R

${bindir}/md 2 $npart $steps $trsnaps ".0001" $mass "0.1 1.0 0.2 0.05 50.0 0.1" 2.5 2.0 $RANDOM md.out $trjout

# Extract the metrics
echo $trsnaps > $metricout
cat md.out | tail -1 | awk '{print $2, $3, $4}' | tr ' ' '\n' >> $metricout

# Clean up
#rm md.out

exit 0


#! /bin/bash

export HOME=$PWD

caseParams=$1
metricout=$HOME/$2
trjout=$HOME/$3

echo $caseParams
echo $metricout
echo $trjout

npart=$(echo $caseParams | tr '|' '\n' | grep npart | awk -F',' '{print $2}')
steps=$(echo $caseParams | tr '|' '\n' | grep steps | awk -F',' '{print $2}')
trsnaps=$(echo $caseParams | tr '|' '\n' | grep trsnaps | awk -F',' '{print $2}')
mass=$(echo $caseParams | tr '|' '\n' | grep mass | awk -F',' '{print $2}')

cd ${0%/*} || exit 1

chmod 777 * -R

./md 2 $npart $steps $trsnaps ".0001" $mass "0.1 1.0 0.2 0.05 50.0 0.1" 2.5 2.0 $RANDOM md.out $trjout

# extract the metrics
echo $trsnaps > $metricout
cat md.out | tail -1 | awk '{print $2, $3, $4}' | tr ' ' '\n' >> $metricout

rm md.out

exit 0


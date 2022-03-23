#!/bin/bash

echo ""
echo "Running Post-Processor..."
echo $@
echo ""

outcsv=$1
outhtml=$2
rpath=$3

colorby="kinetic"

echo $@

if [[ "$rpath" == *"/efs/job_working_directory"* ]];then
	basedir="$(echo /download$rpath | sed "s|/efs/job_working_directory||g" )"
	DEbase="/preview"  
elif [[ "$rpath" == *"/export/galaxy-central"* ]];then 
	basedir="$(echo /download$rpath | sed "s|/export/galaxy-central/database/job_working_directory||g" )"
	DEbase="/preview"  
else
	basedir="$(echo http://dev.parallel.works:8080/preview$rpath | sed "s|/core||g" )"
	DEbase="http://dev.parallel.works:8080/preview/share"
fi 

# write the csv file
python ./models/mexdex/writeDesignExplorerCsv.py --imagesDirectory "results/case_{:d}" cases.list models/mexdex/kpi.json $basedir $outcsv

baseurl="$DEbase/DesignExplorer/index.html?datafile=$basedir/$outcsv&colorby=$colorby"
echo '<html style="overflow-y:hidden;background:white"><a style="font-family:sans-serif;z-index:1000;position:absolute;top:15px;right:0px;margin-right:20px;font-style:italic;font-size:10px" href="'$baseurl'" target="_blank">Open in New Window</a><iframe width="100%" height="100%" src="'$baseurl'" frameborder="0"></iframe></html>' > $outhtml


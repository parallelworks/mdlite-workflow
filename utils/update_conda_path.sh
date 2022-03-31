#!/bin/tcsh
#================================

# The original path to search for/replace
#set old_path = /pw/

# Replace with this path
#set new_path = /scratch/sfg3866/pworks/

set list_of_searches = ( .miniconda3/bin/conda .miniconda3/envs/parsl-pw/bin/process_worker_pool.py .miniconda3/etc .miniconda3/envs/parsl-pw/etc .miniconda3/envs/parsl-pw/conda-meta )

foreach search ( $list_of_searches )
    foreach file ( `find ${search} -type f` )
	sed -i "s|/pw/|/scratch/sfg3866/pworks/|g" $file
	#echo $file
    end
end

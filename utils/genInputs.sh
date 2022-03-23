#!/bin/bash

for f in /pw/storage/gcs_store/gw100_structures/*;do
     echo "<option value=\"$f\">$(basename $f .xyz)</option>"
done
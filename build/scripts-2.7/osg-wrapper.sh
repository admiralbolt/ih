#!/bin/bash
source /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/5.6.2/init/bash

module load python/2.7
module load libgfortran
module load lapack
module load atlas
module load hdf5/1.8.13
module load netcdf/4.2.0
module load gnome_libs
module load ffmpeg/0.10.15
module load opencv/2.4.10
module load image_modules

export PYTHONPATH=./ih-1.0/:$PYTHONPATH
tar -zxf ih.tar.gz
EXECUTABLE="$1"
COMMAND="$@"
### STAND BACK, BASH SCRIPTING ###
while [[ $# > 1 ]]
do
key="$1"
case $key in
    --output)
    OUTPUT="$2"
    shift
    ;;
    *)
            # unknown option
    ;;
esac
shift
done
### Its safe now ###

echo "Executable: $EXECUTABLE, Command: $COMMAND, Output: $OUTPUT"
mkdir -p `dirname "$OUTPUT"`
chmod 755 $EXECUTABLE
eval $COMMAND
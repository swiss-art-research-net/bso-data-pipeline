#!/bin/bash

usage() { echo "Usage: $0 [-i <input folder>] [-o <output folder>] [-m <mapping file>] [-g <generator policy>] [-b <batch size>]" 1>&2; exit 1; }

while getopts ":i:o:m:g:b:" o; do
    case "${o}" in
        i)
            RECORDSINPUTFOLDER=${OPTARG}
            ;;
        o)
            RECORDSOUTPUTFOLDER=${OPTARG}
            ;;
        m)
            RECORDMAPPING=${OPTARG}
            ;;
        g)
            GENERATOR=${OPTARG}
            ;;
        b)
            BATCHSIZE=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

echo "Mapping Records"
numfiles=$(ls -l $RECORDSINPUTFOLDER/*.xml | wc -l)
count=1
echo "Found $numfiles record XML files"

(
for f in $(ls -1 $RECORDSINPUTFOLDER/*.xml); do
  ((i=i%BATCHSIZE)); ((i++==0)) && wait
  echo "Mapping record $count of $numfiles ($f)"
  o=${f/.xml/.ttl}
  o=${o/$RECORDSINPUTFOLDER/}
  java --add-opens java.base/java.lang.reflect=ALL-UNNAMED \
    --add-opens java.base/java.util=ALL-UNNAMED \
    --add-opens java.base/java.text=ALL-UNNAMED \
    --add-opens java.desktop/java.awt.font=ALL-UNNAMED \
    -jar /x3ml/x3ml-engine.exejar \
    --input $f \
    --x3ml $RECORDMAPPING \
    --policy $GENERATOR \
    --output $RECORDSOUTPUTFOLDER/$o \
    --format text/turtle &
  count=$((count+1)) 
done
)
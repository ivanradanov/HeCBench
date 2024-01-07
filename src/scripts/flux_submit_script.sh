#!/bin/bash

set -e
set -x

CURDATE=$(date +"%Y-%m-%dT%H:%M:%S%z")

#FACTORS="1 2 3 4 5 6 7 8 9 10"
DISTRIBUTE_FACTORS="1 2 3 4 5 6 7 8 9 10"
FOR_FACTORS="1 2 3 4 5 6 7 8 9 10"
DYN_CONV="0 1"
TIMEOUT=8h

for d in $DISTRIBUTE_FACTORS; do
for f in $FOR_FACTORS; do
for dc in $DYN_CONV; do
    JOB_NAME="$d-$f-$dc"
    OMP_PROFILE_DIR="$LCWS/results/HeCBench/$CURDATE/omp-profile-$JOB_NAME-dir"
    mkdir -p "$OMP_PROFILE_DIR"
    JOB_LOG_DIR="$LCWS/results/jobs/$CURDATE/"
    mkdir -p "$JOB_LOG_DIR"
    JOB_LOG="$JOB_LOG_DIR/job-$JOB_NAME.out"
    flux submit -N 1 -x -t "$TIMEOUT" --output="$JOB_LOG" ./flux_job.sh "$OMP_PROFILE_DIR" "$d" "$f" "$dc"
done
done
done

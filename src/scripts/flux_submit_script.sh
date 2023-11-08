#!/bin/bash

CURDATE=$(date +"%Y-%m-%dT%H:%M:%S%z")

FACTORS="1 2 4 6 8"
TIMEOUT=8h

for i in $FACTORS; do
    OMP_PROFILE_DIR="$HOME/results/HeCBench/$CURDATE/omp-profile-$i-dir"
    mkdir -p "$OMP_PROFILE_DIR"
    JOB_LOG_DIR="$HOME/results/jobs/$CURDATE/"
    mkdir -p "$JOB_LOG_DIR"
    JOB_LOG="$JOB_LOG_DIR/job-$i.out"
    flux submit -N 1 -x -t "$TIMEOUT" --output="$JOB_LOG" ./flux_job.sh "$i" "$OMP_PROFILE_DIR"

done

#!/bin/bash

set -e
set -x

CURDATE=$(date +"%Y-%m-%dT%H:%M:%S%z")

#FACTORS="1 2 3 4 5 6 7 8 9 10"
FACTORS="1 2"
DYN_CONV="0 1"
#COAL_FRIENDLY="0 1"
COAL_FRIENDLY="0"
IDC="0 1"
TIMEOUT=8h

for dc in $DYN_CONV; do
for i in $FACTORS; do
for cf in $COAL_FRIENDLY; do
for idc in $IDC; do
    JOB_NAME="$dc-$i-$cf-$idc"
    OMP_PROFILE_DIR="$LCWS/results/HeCBench/$CURDATE/omp-profile-$JOB_NAME-dir"
    mkdir -p "$OMP_PROFILE_DIR"
    JOB_LOG_DIR="$LCWS/results/jobs/$CURDATE/"
    mkdir -p "$JOB_LOG_DIR"
    JOB_LOG="$JOB_LOG_DIR/job-$JOB_NAME.out"
    flux submit -N 1 -x -t "$TIMEOUT" --output="$JOB_LOG" ./flux_job.sh "$OMP_PROFILE_DIR" "$i" "$dc" "$cf" "$idc"
done
done
done
done

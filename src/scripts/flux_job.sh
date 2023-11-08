#!/bin/bash

set -e
set -x

i="$1"
OMP_PROFILE_DIR="$2"

CURDATE=$(date +"%Y-%m-%dT%H:%M:%S%z")
HOST=$(hostname)

module load rocm
module load ninja

mkdir -p "/l/ssd/ivanov2/"

ORIGINAL_HECDIR="$HOME/src/HeCBench"
HECDIR="/l/ssd/ivanov2/HeCBench-$HOST-$CURDATE/"
mkdir -p "$HECDIR"
git clone --depth=1 file://"$ORIGINAL_HECDIR" "$HECDIR"
#cp -a "$HOME/src/HeCBench" "$HECDIR"

cd "$HECDIR"
#git restore .

make omp_clean -j 90 -k || true

cd "$HECDIR/src/scripts/"

ls -lat

llvm-build-corona.sh --release
source "$HOME/bin/llvm-enable-corona.sh" --release

command -v clang
command -v clang++

export UNROLL_AND_INTERLEAVE_FACTOR="$i"

rocm-bandwidth-test -s 0 -d 2

./autohecbench.py omp \
    -o /dev/null \
    --bench-data benchmarks/omp-all.json \
    --bench-fails benchmarks/omp-coarsening-comp-fails.txt \
    --timeout 60 \
    --repeat 3 \
    --omp-profile-dir "$OMP_PROFILE_DIR" \
    --verbose \
    --clean \
    --ignore-bench-time

echo END

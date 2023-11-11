#!/bin/bash

set -e
set -x

i="$1"
dc="$2"
OMP_PROFILE_DIR="$3"

RUN_INFO="$OMP_PROFILE_DIR/run_info"

echo "i is $i" &>> "$RUN_INFO"
echo "dc is $dc" &>> "$RUN_INFO"

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

echo "HecBench:" &>> "$RUN_INFO"
git show &>> "$RUN_INFO"

make omp_clean -j 90 -k || true

cd "$HECDIR/src/scripts/"

ls -lat

llvm-build-corona.sh --release
source "$HOME/bin/llvm-enable-corona.sh" --release

echo "clang:" &>> "$RUN_INFO"
command -v clang
command -v clang++

clang --version &>> "$RUN_INFO"
clang++ --version &>> "$RUN_INFO"

export UNROLL_AND_INTERLEAVE_FACTOR="$i"
export UNROLL_AND_INTERLEAVE_DYNAMIC_CONVERGENCE="$dc"

rocm-bandwidth-test -s 0 -d 2

./autohecbench.py omp \
    -o /dev/null \
    --bench-data benchmarks/omp-all.json \
    --bench-fails benchmarks/omp-coarsening-comp-fails.txt \
    --timeout 45 \
    --repeat 3 \
    --omp-profile-dir "$OMP_PROFILE_DIR" \
    --verbose \
    --clean \
    --ignore-bench-time \
    --ignore-failing

echo END

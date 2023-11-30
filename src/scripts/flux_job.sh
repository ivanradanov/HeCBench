#!/bin/bash

set -e
set -x

OMP_PROFILE_DIR="$1"
i="$2"
dc="$3"
cf="$4"
idc="$5"

# Sometimes ccache from different nodes interact badly and things fail
export CCACHE_DISABLE=1

RUN_INFO="$OMP_PROFILE_DIR/run_info"

echo "i is $i" &>> "$RUN_INFO"
echo "dc is $dc" &>> "$RUN_INFO"
echo "cf is $cf" &>> "$RUN_INFO"
echo "idc is $idc" &>> "$RUN_INFO"

CURDATE=$(date +"%Y-%m-%dT%H:%M:%S%z")
HOST=$(hostname)

module load rocm
module load ninja

mkdir -p "/l/ssd/ivanov2/"

ORIGINAL_HECDIR="$LCWS/src/HeCBench"
HECDIR="/l/ssd/$USER/HeCBench-$HOST-$CURDATE/"
mkdir -p "$HECDIR"
git clone --depth=1 file://"$ORIGINAL_HECDIR" "$HECDIR"
cp -a "$ORIGINAL_HECDIR/src/data" "$HECDIR"
cp -a "$ORIGINAL_HECDIR/src/data" "$HECDIR/src/"

cd "$HECDIR"

echo "HecBench:" &>> "$RUN_INFO"
git log -1 &>> "$RUN_INFO"

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

export OMP_OPT_COARSENING_FACTOR="$i"
export OMP_OPT_COARSENING_DYNAMIC_CONVERGENCE="$dc"
export OMP_OPT_COARSENING_COALESCING_FRIENDLY="$cf"
export OMP_OPT_COARSENING_INCREASE_DISTRIBUTE_CHUNKING="$idc"

rocm-bandwidth-test -s 0 -d 2

./autohecbench.py omp \
    -o /dev/null \
    --bench-data benchmarks/omp-all.json \
    --bench-fails benchmarks/omp-coarsening-comp-fails.txt \
    --timeout 45 \
    --repeat 3 \
    --omp-profile-dir "$OMP_PROFILE_DIR" \
    --clean \
    --ignore-bench-time \
    --ignore-failing

#    --verbose \

CURDATE="$(date +"%Y-%m-%dT%H:%M:%S%z")"
echo END "$CURDATE"

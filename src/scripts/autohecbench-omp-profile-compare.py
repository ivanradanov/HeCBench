#!/usr/bin/env python3

import argparse
import json
import os
import sys
import glob
import statistics
import natsort

def print_table(table):
    longest_cols = [
        (max([len(str(row[i])) for row in table]) + 3)
        for i in range(len(table[0]))
    ]
    row_format = "".join(["{:>" + str(longest_col) + "}" for longest_col in longest_cols])
    for row in table:
        print(row_format.format(*row))

def get_timings(prof_dirs):
    all_timings = {}
    for prof_dir in prof_dirs:
        sorted_bench_dirs = sorted(os.listdir(prof_dir))
        all_timings[prof_dir] = {}
        for bench_dir in sorted_bench_dirs:
            abs_bench_dir = os.path.join(prof_dir, bench_dir)
            if not os.path.isdir(abs_bench_dir):
                print('found non dir {}'.format(abs_bench_dir), file=sys.stderr)
                continue
            timings = all_timings[prof_dir][bench_dir] = {}
            for prof_file in glob.glob(abs_bench_dir + "/openmp.profile*.out*"):
                abs_prof_file = os.path.join(abs_bench_dir, prof_file)
                f = open(abs_prof_file)
                try:
                    res = json.load(f)
                except:
                    print('load from {} failed'.format(abs_prof_file), file=sys.stderr)
                    continue
                f.close()

                for ev in res['traceEvents']:
                    if ev['name'] != 'targetKernel':
                        continue
                    pid = ev['pid']
                    if pid not in timings:
                        timings[pid] = {}
                    kernel_name = ev['args']['detail']
                    if kernel_name not in timings[pid]:
                        timings[pid][kernel_name] = []
                    timings[pid][kernel_name].append(ev['dur'])

    all_kernel_timings = {}
    for prof, prof_timings in all_timings.items():
        all_kernel_timings[prof] = {}
        for bench, bench_timings in prof_timings.items():
            for pid, pid_timings in bench_timings.items():
                for kernel, kernel_timings in pid_timings.items():
                    uniq_kernel_name = bench + kernel
                    if uniq_kernel_name not in all_kernel_timings[prof]:
                        all_kernel_timings[prof][uniq_kernel_name] = []
                    pid_kernel_timing = sum(kernel_timings)
                    all_kernel_timings[prof][uniq_kernel_name].append(pid_kernel_timing)

    for prof, prof_timings in all_kernel_timings.items():
        for kernel, timing in prof_timings.items():
            all_kernel_timings[prof][kernel] = statistics.median(timing) if len(timing) != 0 else None

    profs = set()
    kernels = set()
    for prof, prof_timings in all_kernel_timings.items():
        profs.add(prof)
        for kernel, timing in prof_timings.items():
            kernels.add(kernel)

    return profs, kernels, all_kernel_timings

def main():
    parser = argparse.ArgumentParser(description='Benchmarks comparisons')

    parser.add_argument('input', nargs='*',
                        help='Benchmark result dirs to compute speedup between (BASELINE vs 1, 2, ...)')

    args = parser.parse_args()

    profs, kernels, all_kernel_timings = get_timings(args.input)

    print_data = [[os.path.basename(prof) for prof in profs]]
    for kernel in kernels:
        ts = []
        for prof in profs:
            ts.append(None if kernel not in all_kernel_timings[prof] else all_kernel_timings[prof][kernel])
        row = []
        for i in range(len(ts)):
            if i == 0:
                row.append(kernel)
            else:
                if ts[0] is None or ts[i] is None:
                    speedup = '-'
                else:
                    speedup = ts[0] / ts[i]
                row.append('-' if speedup == '-' else '{:.2f}'.format(speedup))

        print_data.append(row)

    print_table(print_data)




if __name__ == "__main__":
    main()

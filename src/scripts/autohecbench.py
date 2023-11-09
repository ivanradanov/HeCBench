#!/usr/bin/env python3
#
# Script to run HeCBench benchmarks and gather results

import re, time, sys, subprocess, multiprocessing, os
import argparse
import json


class Benchmark:
    def __init__(self, args, name, res_regex, run_args = [], binary = "main", invert = False):
        if name.endswith('sycl'):
            self.MAKE_ARGS = ['GCC_TOOLCHAIN="{}"'.format(args.gcc_toolchain)]
            if args.sycl_type == 'cuda':
                self.MAKE_ARGS.append('CUDA=yes')
                self.MAKE_ARGS.append('CUDA_ARCH=sm_{}'.format(args.nvidia_sm))
            elif args.sycl_type == 'hip':
                self.MAKE_ARGS.append('HIP=yes')
                self.MAKE_ARGS.append('HIP_ARCH={}'.format(args.amd_arch))
            elif args.sycl_type == 'opencl':
                self.MAKE_ARGS.append('CUDA=no')
                self.MAKE_ARGS.append('HIP=no')
        elif name.endswith('cuda'):
            self.MAKE_ARGS = ['CUDA_ARCH=sm_{}'.format(args.nvidia_sm)]
        elif name.endswith('omp'):
            self.MAKE_ARGS = ['-f', 'Makefile.{}'.format('aomp')]
            self.MAKE_ARGS.append('ARCH={}'.format('gfx906'))
            self.MAKE_ARGS.append('DEVICE={}'.format('gpu'))
        else:
            self.MAKE_ARGS = []

        if args.extra_compile_flags:
            flags = args.extra_compile_flags.replace(',',' ')
            self.MAKE_ARGS.append('EXTRA_CFLAGS={}'.format(flags))

        if args.bench_dir:
            self.path = os.path.realpath(os.path.join(args.bench_dir, name))
        else:
            self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', name)

        self.name = name
        self.binary = binary
        self.res_regex = res_regex
        self.args = run_args
        self.invert = invert
        self.clean = args.clean
        self.verbose = args.verbose
        self.timeout = args.timeout
        self.pargs = args

    def compile(self):
        if self.clean:
            subprocess.run(["make", "clean"] + self.MAKE_ARGS, cwd=self.path).check_returncode()
            time.sleep(1) # required to make sure clean is done before building, despite run waiting on the invoked executable

        out = subprocess.DEVNULL
        if self.verbose:
            out = subprocess.PIPE

        proc = subprocess.run(["make"] + self.MAKE_ARGS, cwd=self.path, stdout=out, stderr=subprocess.STDOUT, encoding="ascii")
        try:
            proc.check_returncode()
        except subprocess.CalledProcessError as e:
            print(f'Failed compilation in {self.path} with args {self.MAKE_ARGS}.\n{e}')
            if e.stderr:
                print(e.stderr, file=sys.stderr)
            if not self.pargs.ignore_failing:
                raise(e)

        if self.verbose:
            print(proc.stdout)

    def run(self):
        cmd = ['make' if self.binary == 'make' else './' + self.binary] + self.args
        env = os.environ
        if self.pargs.omp_profile_dir:
            output_dir = os.path.join(self.pargs.omp_profile_dir, self.name)
            if not os.path.isdir(output_dir):
                os.mkdir(output_dir)
            output_file = os.path.join(output_dir, "openmp.profile.out")
            env['LIBOMPTARGET_PROFILE'] = output_file
        if self.verbose:
            print(" ".join(cmd), flush=True)
        try:
            proc = subprocess.run(cmd, cwd=self.path, stdout=subprocess.PIPE,
                                  encoding="ascii", timeout=self.timeout, env=env)
        except subprocess.CalledProcessError as e:
            if self.pargs.ignore_failing:
                return 0.0
            raise(e)
        out = proc.stdout
        if self.verbose:
            print(out, flush=True)
        if self.pargs.ignore_bench_time:
            return 0.0
        res = re.findall(self.res_regex, out)
        if not res:
            if self.pargs.ignore_failing:
                return 0.0
            raise Exception(self.path + ":\nno regex match for " + self.res_regex + " in\n" + out)
        res = sum([float(i) for i in res]) #in case of multiple outputs sum them
        if self.invert:
            res = 1/res
        return res


def comp(b):
    print("compiling: {}".format(b.name), flush=True)
    b.compile()

def main():
    parser = argparse.ArgumentParser(description='HeCBench runner')
    parser.add_argument('--output', '-o',
                        help='Output file for csv results')
    parser.add_argument('--repeat', '-r', type=int, default=1,
                        help='Repeat benchmark run')
    parser.add_argument('--warmup', '-w', type=bool, default=True,
                        help='Run a warmup iteration')
    parser.add_argument('--sycl-type', '-s', choices=['cuda', 'hip', 'opencl'], default='cuda',
                        help='Type of SYCL device to use')
    parser.add_argument('--nvidia-sm', type=int, default=60,
                        help='NVIDIA SM version')
    parser.add_argument('--amd-arch', default='gfx908',
                        help='AMD Architecture')
    parser.add_argument('--gcc-toolchain', default='',
                        help='GCC toolchain location')
    parser.add_argument('--extra-compile-flags', '-e', default='',
                        help='Additional compilation flags (inserted before the predefined CFLAGS)')
    parser.add_argument('--clean', '-c', action='store_true',
                        help='Clean the builds')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Clean the builds')
    parser.add_argument('--bench-dir', '-b',
                        help='Benchmark directory')
    parser.add_argument('--bench-data', '-d',
                        help='Benchmark data')
    parser.add_argument('--bench-fails', '-f',
                        help='List of failing benchmarks to ignore')
    parser.add_argument('--timeout', type=int, default=300,
                        help='Time to wait before killing a benchmark in seconds')
    parser.add_argument('--omp-profile-dir', default=None,
                        help='filename to dump profile info to')
    parser.add_argument('--ignore-bench-time', action='store_true',
                        help='ignore time output by benchmark')
    parser.add_argument('--ignore-failing', action='store_true',
                        help='Ignore failing benchmarks')
    parser.add_argument('bench', nargs='+',
                        help='Either specific benchmark name or sycl, cuda, or hip')

    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Load benchmark data
    if args.bench_data:
        bench_data = args.bench_data
    else:
        bench_data = os.path.join(script_dir, 'benchmarks', 'subset.json') 

    with open(bench_data) as f:
        benchmarks = json.load(f)

    # Load fail file
    if args.bench_fails:
        bench_fails = os.path.abspath(args.bench_fails)
    else:
        bench_fails = os.path.join(script_dir, 'benchmarks', 'subset-fails.txt')

    with open(bench_fails) as f:
        fails = f.read().splitlines()

    # Build benchmark list
    benches = []
    for b in args.bench:
        if b in ['sycl', 'cuda', 'hip', 'omp']:
            benches.extend([Benchmark(args, k, *v)
                            for k, v in benchmarks.items()
                            if k.endswith(b) and k not in fails])
            continue

        benches.append(Benchmark(args, b, *benchmarks[b]))

    t0 = time.time()
    try:
        with multiprocessing.Pool() as p:
            p.map(comp, benches, chunksize=1)
    except Exception as e:
        print("Compilation failed, exiting")
        print(e, flush=True)
        sys.exit(1)

    t_compiled = time.time()

    outfile = sys.stdout
    if args.output:
        outfile = open(args.output, 'w')

    for b in benches:
        try:
            if args.verbose:
                print("running: {}".format(b.name), flush=True)

            if args.warmup:
                b.run()

            res = []
            for i in range(args.repeat):
                res.append(str(b.run()))

            print(b.name + "," + ", ".join(res), file=outfile)
        except Exception as err:
            print("Error running: ", b.name)
            print(err)

    if args.output:
        outfile.close()

    t_done = time.time()
    print("compilation took {} s, runnning took {} s.".format(t_compiled-t0, t_done-t_compiled))

if __name__ == "__main__":
    main()


OMP_DIRS := $(shell find src -name *-omp)

omp: $(addsuffix .omp,$(OMP_DIRS))
omp_run: $(addsuffix .omp.run,$(OMP_DIRS))
omp_clean: $(addsuffix .omp.clean,$(OMP_DIRS))

%.omp:
	$(MAKE) -C $* -f Makefile.aomp

%.omp.run:
	$(MAKE) -C $* -f Makefile.aomp run

%.omp.clean:
	$(MAKE) -C $* -f Makefile.aomp clean

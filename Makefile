
here = $(shell pwd)

# include ulab in firmware
SHELL := /bin/bash
export USER_C_MODULES := ${here}/firmware/ulab
# include ubdsim as a frozen module for all builds
export FROZEN_MANIFEST := ${here}/frozen_manifest.py
# build with multiple cores
NPROC := $(shell python3 -c 'import multiprocessing; print(multiprocessing.cpu_count())')

make = make -j${NPROC:}
micropython_dir = ${here}/firmware/micropython

general: init unix stubs

init:
	git submodule update --init
	cd firmware/ulab && \
		git submodule update --init --recursive

stubs:
	python3 extract_stubs_ulab.py firmware/ulab/code .micropy/ulab/ulab

# unix port
unix: _qstr-defs
	cd ${micropython_dir}/ports/unix && \
		$(make) submodules && \
		$(make) deplibs && \
		$(make) all

micropython=${micropython_dir}/ports/unix/micropython

unix-fresh:
	cd ${micropython_dir}/ports/unix && \
		$(make) clean && \
		$(make) clean-frozen
	$(make) unix

unix-repl: unix
	$(micropython)

unix-test: unix
	# MICROPYPATH="" fixes a weird import issue
	# https://github.com/micropython/micropython/issues/2322#issuecomment-277845841
	MICROPYPATH="" $(micropython) test_ubdsim.py

# esp32 port
esp32: _qstr-defs
	cd ${here}/firmware/esp-idf && \
		git submodule update --init --recursive && \
		export IDF_PATH=$$(pwd) && \
		export IDF_TOOLS_PATH=${here}/firmware/idf-tools && \
		\
		./install.sh && \
		. ./export.sh && \
		\
		cd ${micropython_dir}/ports/esp32 && \
			export BOARD=GENERIC && \
			\
			$(make) submodules && \
			$(make) all

esp32-fresh:
	cd ${micropython_dir}/ports/esp32 && \
		rm -rf ${micropython_dir}/ports/esp32/build-GENERIC && \
		$(make) clean && \
		$(make) erase
	$(make) esp32

esp32-deploy: esp32
	cd ${micropython_dir}/ports/esp32 && \
		$(make) deploy

esp32-repl: esp32-deploy
	rshell -p /dev/ttyUSB0 cd /pyboard; repl


# all these source files must be mpy-cross-compiled into bytecode
# and then frozen as c code so that the libraries are stored in ROM
UBDSIM_PY_SRC=$(call _rwildcard,ubdsim,*.py)
UBDSIM_RT_PY_SRC=$(call _rwildcard,ubdsim_realtime,*.py)

# all the bytecode from ubdsim and ubdsim_realtime
dist: $(wildcard ubdsim_realtime/**/*.py) $(wildcard ubdsim/**/*.py) _mpy-cross
	# can't use these as proper dependencies - make has no dynamic dependency evaluation :(
	# have to do it manually
	set -e && \
		for target in $(addprefix firmware/bytecode/,$(UBDSIM_PY_SRC:.py=.mpy) $(UBDSIM_RT_PY_SRC:.py=.mpy)); \
		do \
			if ! echo "$${target}" | egrep -q ".*test_\w*\.mpy"; then \
				echo $(make) -s $${target}; \
				$(make) -s $${target}; \
			fi \
		done
	
	cd firmware/bytecode && \
		python3 setup.py sdist

# cross-compiled micropython bytecode
# for any targets with `ubdsim/*`, retarget to `ubdsim/bdsim/*`
# should really depend on 'mpy-cross', and kinda does as long as this is only made from the above for loop
firmware/bytecode/%.mpy: %.py
	# target directory must exist or it fails silently
	mkdir -p $$(dirname $@)
	# do the cross-compilation
	set -e && \
		${micropython_dir}/mpy-cross/mpy-cross -O 3 -o $@ $<

_qstr-defs: _mpy-cross # alias for clarity

_mpy-cross:
	# ensures mpy-cross is updated with the latest QSTR definitions from USER_C_MODULES
	$(make) V=1 -C ${micropython_dir}/mpy-cross

# function to recursively list files matching glob pattern.
# https://stackoverflow.com/a/18258352/1266662
_rwildcard=$(foreach d,$(wildcard $(1:=/*)),$(call _rwildcard,$d,$2) $(filter $(subst *,%,$2),$d))
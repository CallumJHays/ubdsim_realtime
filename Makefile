
here = $(shell pwd)

# include ulab in firmware
SHELL := /bin/bash
export USER_C_MODULES ?= ${here}/firmware/ulab
# include ubdsim as a frozen module for all builds
export FROZEN_MANIFEST ?= ${here}/frozen_manifest.py
export ESPIDF ?= ${here}/firmware/esp-idf
export PATH := ${here}/firmware/xtensa-esp32-elf/bin:${PATH}
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
unix: .build-flags/unix
.build-flags/unix: .build-flags/qstr-defs .build-flags/src-code
	cd ${micropython_dir}/ports/unix && \
		$(make) submodules && \
		$(make) deplibs && \
		$(make) all
	touch $@

micropython=${micropython_dir}/ports/unix/micropython

unix-fresh:
	rm -f .build-flags/unix
	cd ${micropython_dir}/ports/unix && \
		$(make) clean && \
		$(make) clean-frozen
	$(make) unix

unix-repl: .build-flags/unix
	$(micropython)

unix-test: .build-flags/unix
	# MICROPYPATH="" fixes a weird import issue
	# https://github.com/micropython/micropython/issues/2322#issuecomment-277845841
	MICROPYPATH="" $(micropython) rlc_experiment.py


.build-flags/unix-unfrozen: .build-flags/qstr-defs
	$(make) unix
	touch $@

unix-unfrozen-test: .build-flags/unix-unfrozen
	# MICROPYPATH="" fixes a weird import issue
	# https://github.com/micropython/micropython/issues/2322#issuecomment-277845841
	MICROPYPATH="src:.upip-deps" $(micropython) rlc_experiment.py


esp32-clean-mpy:
	rm -rf ${micropython_dir}/ports/esp32/build-GENERIC/frozen_mpy
	rm -f .build-flags/esp32*

# esp32 port
esp32: .build-flags/esp32
.build-flags/esp32: .build-flags/qstr-defs .build-flags/src-code frozen_manifest.py
	cd ${ESPIDF} && \
		git submodule sync --recursive && \
		git submodule update --init --recursive && \
		\
		# for < v1.14 \
		pip install -r requirements.txt && \
		\
		# attempted for v1.14 install. Leaving here for now. \
		# export IDF_PATH=$$(pwd) && \
		# export IDF_TOOLS_PATH=${here}/firmware/idf-tools && \
		# ./install.sh && \
		# . ./export.sh && \
		\
		cd ${micropython_dir}/ports/esp32 && \
			export BOARD=GENERIC && \
			export FROZEN_MANIFEST_INCLUDE=$$(pwd)/boards/manifest.py && \
			\
			$(make) all
	touch $@

esp32-clean:
	rm -f .build-flags/esp32*
	cd ${micropython_dir}/ports/esp32 && \
		rm -rf ${micropython_dir}/ports/esp32/build-GENERIC && \
		\
		$(make) clean && \
		$(make) clean-frozen

esp32-deploy: .build-flags/esp32-deployed
.build-flags/esp32-deployed: .build-flags/esp32
	cd ${micropython_dir}/ports/esp32 && \
		\
		# not the best way to do this but a quick fix and works - \
		# allocate more partition space to ROM over FS \
		cp ${here}/esp32_partitions.csv ./partitions.csv && \
		\
		export BOARD=GENERIC && \
		export FROZEN_MANIFEST_INCLUDE=$$(pwd)/boards/manifest.py && \
		$(make) deploy
	touch $@

esp32-run-example-%: .build-flags/esp32-deployed
	rshell -p /dev/ttyUSB0 "\
		cp examples/boot.py /pyboard/; \
		cp examples/$*.py /pyboard/; \
		cd /pyboard; \
		repl ~ import $*"

esp32-repl: .build-flags/esp32-deployed
	rshell -p /dev/ttyUSB0 "cd /pyboard; repl"


# all these source files must be mpy-cross-compiled into bytecode
# and then frozen as c code so that the libraries are stored in ROM
UBDSIM_PY_SRC=$(shell find -L src/bdsim -name '*.py')
UBDSIM_RT_PY_SRC=$(shell find -L src/bdsim_realtime -name '*.py')
UPIP_DEPS=$(shell find -L .upip-deps -name '*.py')

# all the bytecode from ubdsim and ubdsim_realtime
dist: _src-code _mpy-cross
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

.build-flags/src-code: $(UBDSIM_PY_SRC) $(UBDSIM_RT_PY_SRC) $(UPIP_DEPS)
	touch $@

# cross-compiled micropython bytecode
# for any targets with `ubdsim/*`, retarget to `ubdsim/bdsim/*`
# should really depend on 'mpy-cross', and kinda does as long as this is only made from the above for loop
firmware/bytecode/%.mpy: %.py
	# target directory must exist or it fails silently
	mkdir -p $$(dirname $@)
	# do the cross-compilation
	set -e && \
		${micropython_dir}/mpy-cross/mpy-cross -O 3 -o $@ $<

.build-flags/mpy-cross: $(wildcard firmware/ulab/**/*.(ch)) $(wildcard firmware/ulab/**/*.h)
	# ensures mpy-cross is updated with the latest QSTR definitions from USER_C_MODULES
	$(make) V=1 -C ${micropython_dir}/mpy-cross
	touch $@

# alias for clarity. qstr defs get commpiled by mpy-cross
.build-flags/qstr-defs: .build-flags/mpy-cross
	touch $@

# function to recursively list files matching glob pattern.
# https://stackoverflow.com/a/18258352/1266662
_rwildcard=$(foreach d,$(wildcard $(1:=/*)),$(call _rwildcard,$d,$2) $(filter $(subst *,%,$2),$d))
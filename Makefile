root=$(shell pwd)
micropython_dir=${root}/firmware/micropython

# include ulab in firmware
export USER_C_MODULES=${root}/firmware/ulab

# build with multiple cores
NPROC:=$(shell python3 -c 'import multiprocessing; print(multiprocessing.cpu_count())')
make=make -j${NPROC:}

# unix port
unix:
	cd ${micropython_dir}/ports/unix && \
		\
		$(make) clean-frozen && \
		rm -rf modules && \
		mkdir -p modules && \
		./micropython -m upip install -p modules picoweb && \
		cp -r ${root}/ubdsim modules/ && \
		cp -r ${root}/ubdsim_realtime modules/ && \
		\
		$(make) clean && \
		$(make) submodules && \
		$(make) deplibs && \
		$(make) all FROZEN_MPY_DIR=modules

micropython=${micropython_dir}/ports/unix/micropython

unix-repl: unix
	$(micropython)

unix-test: unix
	$(micropython) test_ubdsim.py

# esp32 port
esp32:
	cd ${micropython_dir}/ports/esp32 && \
		\
		export PATH=${root}/firmware/xtensa-esp32-elf/bin:$$PATH && \
		export ESPIDF=${root}/firmware/esp-idf && \
		export BOARD=GENERIC && \
		\
		$(make) clean && \
		$(make) submodules && \
		$(make) all

esp32-repl:
	rshell -p /dev/ttyUSB0 cd /pyboard; repl

stubs:
	python extract_pyi.py ${root}/firmware/ulab/code .micropy/ulab


# all these source files must be mpy-cross-compiled into bytecode
# and then frozen as c code so that the libraries are stored in ROM
UBDSIM_PY_SRC=$(call _rwildcard,ubdsim,*.py)
UBDSIM_RT_PY_SRC=$(call _rwildcard,ubdsim_realtime,*.py)

# all the bytecode from ubdsim and ubdsim_realtime
dist: $(wildcard ubdsim_realtime/**/*.py) $(wildcard ubdsim/**/*.py) _unix-base
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
# foor any targets with `ubdsim/*`, retarget to `ubdsim/bdsim/*`
firmware/bytecode/%.mpy: %.py
	# target directory must exist or it fails silently
	mkdir -p $$(dirname $@)
	# do the cross-compilation
	set -e && \
		${micropython_dir}/mpy-cross/mpy-cross -o $@ $<

# cross-compiler - this handle's qstr generation for c modules too
_mpy-cross:
	$(make) -C ${micropython_dir}/mpy-cross

# an initial build is required to call `micropython -m pip` which is needed to freeze the package
_unix-base: _mpy-cross
	cd ${micropython_dir}/ports/unix && \
		$(make) submodules && $(make) deplibs && $(make) all

# function to recursively list files matching glob pattern.
# https://stackoverflow.com/a/18258352/1266662
_rwildcard=$(foreach d,$(wildcard $(1:=/*)),$(call _rwildcard,$d,$2) $(filter $(subst *,%,$2),$d))
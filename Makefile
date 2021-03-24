FWARE_DIR=$(shell pwd)/firmware

# include ulab in firmware
export USER_C_MODULES=${FWARE_DIR}/ulab

# unix port
unix: firmware/dist
	cd ${FWARE_DIR}/micropython/ports/unix && \
		./micropython -m upip install -p modules ${FWARE_DIR}/dist && \
		make submodules && make deplibs && make all

unix-repl: unix
	${FWARE_DIR}/micropython/ports/unix/micropython

# esp32 port
esp32: firmware/dist
	cd ${FWARE_DIR}/micropython/ports/esp32 && \
		\
		export PATH=${FWARE_DIR}/xtensa-esp32-elf/bin:$$PATH && \
		export ESPIDF=${FWARE_DIR}/esp-idf && \
		export BOARD=GENERIC && \
		\
		make submodules && make all

stubs:
	python extract_pyi.py ${FWARE_DIR}/ulab/code .micropy/ulab

# all these source files must be mpy-cross-compiled into bytecode
# and then frozen as c code so that the libraries are stored in ROM
UBDSIM_PY_SRC=$(call _rwildcard,ubdsim,*.py)
UBDSIM_RT_PY_SRC=$(call _rwildcard,ubdsim-realtime,*.py)

test: firmware/dist

# all the bytecode from ubdsim and ubdsim-realtime
firmware/dist: $(wildcard ubdsim-realtime/**/*.py) $(wildcard ubdsim/**/*.py) _unix-base
	# can't use these as dependencies - make has no dynamic dependency evaluation :(
	# have to do it manually
	for TARGET in $(addprefix firmware/bytecode/,$(UBDSIM_PY_SRC:.py=.mpy) $(UBDSIM_RT_PY_SRC:.py=.mpy)); \
	do \
		echo make -s $${TARGET}; \
		make -s $${TARGET}; \
	done

# cross-compiled micropython bytecode
# foor any targets with `ubdsim/*`, retarget to `ubdsim/bdsim/*`
firmware/bytecode/%.mpy: %.py
	${FWARE_DIR}/micropython/mpy-cross/mpy-cross $< -o $@

# cross-compiler
_mpy-cross:
	make -C ${FWARE_DIR}/micropython/mpy-cross

# an initial build is required to call `micropython -m pip` which is needed to freeze the package
_unix-base: _mpy-cross
	cd ${FWARE_DIR}/micropython/ports/unix && \
		make submodules && make deplibs && make all

# function to recursively list files matching glob pattern.
# https://stackoverflow.com/a/18258352/1266662
_rwildcard=$(foreach d,$(wildcard $(1:=/*)),$(call _rwildcard,$d,$2) $(filter $(subst *,%,$2),$d))
BUILD_DIR=$(shell pwd)/firmware

# include ulab in firmware
export USER_C_MODULES=${BUILD_DIR}/ulab

stubs:
	python extract_pyi.py firmware/ulab/code .micropy/ulab

unix:
	cd ${BUILD_DIR}/micropython/ports/unix && \
		make submodules && make all

esp32:
	cd ${BUILD_DIR}/micropython/ports/esp32 && \
		\
		export PATH=${BUILD_DIR}/xtensa-esp32-elf/bin:$$PATH && \
		export ESPIDF=${BUILD_DIR}/esp-idf && \
		export BOARD=GENERIC && \
		\
		make submodules && make all
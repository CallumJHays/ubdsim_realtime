# `bdsim.micropython`

IO Blocks and a `realtime.run()` implementation optimized for micropython devices.

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/43713e0b78f547e8912ff05c9350cffb)](https://app.codacy.com/app/callumjhays/bdsim.micropython?utm_source=github.com&utm_medium=referral&utm_content=callumjhays/bdsim.micropython&utm_campaign=Badge_Grade_Dashboard)

[![Python](https://img.shields.io/badge/Python-3.6%2B-red.svg)](https://www.python.org/downloads/)

[![saythanks](https://img.shields.io/badge/say-thanks-ff69b4.svg)](https://saythanks.io/to/callumjhays)

BDSim port in micropython for the ESP32

# Installation

`numpy` doesn't exist/work for micropython, but is required by `bdsim`. Instead we use `ulab`, which provides a subset of the `numpy` API for use on micropython devices. `ulab` must be compiled from C code with the micropython firmware - it cannot be packaged by `upip`.

## On Ports with `ulab` pre-installed

If `ulab` is already installed you your target micropython device, `bdsim.micropython` may be installed through `upip`. This is the case with most `circuitpython` boards and `OpenMV`.

<!-- TODO: add links -->

While quick and easy to install, this method stores `bdsim` code in RAM rather than ROM - which is not ideal for resource-limited devices.

For devices with internet access:

```python
# run on micropython device
>> import upip
>> upip.install('bdsim.micropython') # install it
>> import bdsim, bdsim.micropython
>> bd = bdsim.BlockDiagram() # use it
```

For devices without internet access, `bdsim.micropython` can instead be cross-installed and then transferred into the root device directory. Follow the [Micropython Docs](https://docs.micropython.org/en/latest/reference/packages.html#cross-installing-packages) on how to achieve this, substituting `bdsim.micropython` for the package name used in the tutorial. However if you're going through the trouble of this you might as well use the firmware (see below)

## Pre-Built Firmware

We (should) provide pre-built versions of micropython with `ulab` and other frozen modules required by `bdsim.micropython` for ports included in the [Official MicroPython Repository](https://github.com/micropython/micropython/tree/master/ports). We (should) provide two versions per supported port; with both minimum required and full `ulab` features/submodules.

## Building Firmware Manually

These commands assume to be run on linux with access to required dependencies. Please see [The MicroPython README for more information](https://github.com/micropython/micropython#external-dependencies).

### For ESP32

```bash
BUILD_DIR=$(pwd)/firmware # specify build dir
git clone https://github.com/micropython/micropython $BUILD_DIR/micropython
cd $BUILD_DIR/micropython
git checkout b137d064e9e0bfebd2a59a9b312935031252e742
# choose micropython version - note v1.12 is incompatible with ulab
# and v1.13 is currently broken in some ways (on some platforms) https://github.com/BradenM/micropy-cli/issues/167
# - the patch is not live yet (should be in 1.14), but is at this commit
git submodule update --init
cd $BUILD_DIR/micropython/mpy-cross && make # build cross-compiler (required)

cd $BUILD_DIR/micropython/ports/esp32
make ESPIDF= # will display supported ESP-IDF commit hashes
# output should look like: """
# ...
# Supported git hash (v3.3): 9e70825d1e1cbf7988cf36981774300066580ea7
# Supported git hash (v4.0) (experimental): 4c81978a3e2220674a432a588292a4c860eef27b
# """
```

Choose an ESPIDF version from one of the options printed by the previous command:

```bash
ESPIDF_VER=9e70825d1e1cbf7988cf36981774300066580ea7

# Download and prepare the SDK
git clone https://github.com/espressif/esp-idf.git $BUILD_DIR/esp-idf
cd $BUILD_DIR/esp-idf
git checkout $ESPIDF_VER
git submodule update --init --recursive # get idf submodules
pip install -r ./requirements.txt # install python reqs
```

Next, install the ESP32 compiler. If using an ESP-IDF version >= 4.x (chosen by `$ESPIDF_VER` above), this can be done by running `esp-idf/install.sh`. Otherwise, (for version 3.x) run:

```bash
cd $BUILD_DIR

# for 64 bit linux
curl https://dl.espressif.com/dl/xtensa-esp32-elf-linux64-1.22.0-80-g6c4433a-5.2.0.tar.gz | tar xvz

# for 32 bit
# curl https://dl.espressif.com/dl/xtensa-esp32-elf-linux32-1.22.0-80-g6c4433a-5.2.0.tar.gz | tar xvz

# don't worry about adding to path; we'll specify that later

# also, see https://docs.espressif.com/projects/esp-idf/en/v3.3.2/get-started for more info (if you run into problems)
```

Next, download `ulab`'s source code and configure required features:

TODO: indicate minimum `ulab` features required by `bdsim.micropython`

```bash
git clone https://github.com/v923z/micropython-ulab $BUILD_DIR/ulab
cd $BUILD_DIR/ulab
# this commit hash is v1.6.0
git checkout b52292919bc0e02f99c0c377ca96d8f4d6884832

# you can look through and enable/disable ulab features by editing $BUILD_DIR/ulab/code/ulab.h
# the default enables all features
```

Finally, build the firmware:

```bash
cd $BUILD_DIR/micropython/ports/esp32
# temporarily add esp32 compiler to path
export PATH=$BUILD_DIR/xtensa-esp32-elf/bin:$PATH
export ESPIDF=$BUILD_DIR/esp-idf # req'd by Makefile
export BOARD=GENERIC # options are dirs in ./boards
export USER_C_MODULES=$BUILD_DIR/ulab # include ulab in firmware

make submodules & make all
```

Plug in your ESP32 via USB and then flash it:

```bash
make erase && make deploy
```

# Development

A conda environment is provided with a CPython version closest to the equivalent micropython available; 3.4 (as of writing), as well as the micropython interpreter itself built with `ulab` using similar to steps above (for unix).

The CPython will aid development as you will get the same syntax errors in your editor as on your device. You should set your editor's language server's interpreter to this one for that to work. Note that this isn't foolproof - use of standard library may be different in MPy compared to CPy.

The MicroPython interpreter can be used to run tests on unix and distribute this package as a upip installable. The installable can be used to quickly run tests on your device.

Install conda environment:

```bash
conda env update -f environment.yml
```

Run tests on unix:

```bash
# TODO: probably a bash script
```

Run tests on device:

```bash
# TODO: also probably a bash script
# 1. use mpy-cross to produce .mpy modules for dist. pkgs and tests
# 2. upload to device via rshell
# 3. run tests on device

# Note that the above method requires enough RAM to store bdsim.micropython, which may not be viable. Alternatively:
# 1. recompile firmware with bdsim.micropython as frozen module. Reflash device.
# 2. use mpy-cross to produce .mpy modules for tests
# 3. upload to device via rshell
# 4. run tests on device

# A third hybrid approach may also be viable. Keep modules small so that individual frozen modules on the device may be 'overridden' by a local (changed) .mpy module for testing. If an OOM error occurs, recompile the entire module as frozen in firmware and reflash the device. Rinse and repeat.
```

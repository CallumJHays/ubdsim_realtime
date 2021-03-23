from setuptools import find_namespace_packages
import sys
sys.path.append('../../')
from shared_setup import setup_pkg  # nopep8

setup_pkg(
    name='bdsim.micropython',
    packages=find_namespace_packages(),
    description='MicroPython IO blocks and realtime executor',
    install_requires=['bdsim.core']
)

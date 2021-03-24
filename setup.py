from setuptools import setup, find_packages
from os import path
import sdist_upip

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    # this cmd compiles it to a micropython dist package
    # which can then be frozen into firmware if need be
    cmdclass={'sdist': sdist_upip.sdist},

    name='ubdsim',

    version='0.0.1',

    # This is a one-line description or tagline of what your project does. This
    # corresponds to the "Summary" metadata field:
    description="Micropython port of Peter Corke's bdsim - realtime only (no simulation).'",

    long_description=long_description,
    long_description_content_type='text/markdown',

    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: MicroPython :: 1.13'],

    project_urls={
        'Source': 'https://github.com/callumjhays/ubdsim',
        'Tracker': 'https://github.com/callumjhays/ubdsim/issues'
    },

    url='https://github.com/callumjhays/ubdsim',

    author='Callum Hays',

    author_email='callumjhays@gmail.com',  # TODO

    keywords='micropython control-theory PID block-diagram simulink s-plane realtime state-space telemetry tuning',

    license='MIT',

    packages=['ubdsim', 'ubdsim-realtime'],

)

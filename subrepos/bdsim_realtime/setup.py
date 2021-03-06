from setuptools import setup, find_packages
import os
from os import path


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


def recursively_list_all_files(directory: str):
    paths = []
    for (path, _, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


setup(

    name='bdsim_realtime',

    version="0.0.1",

    description='Real-time execution and remote monitoring and tuning of BDSim Block-Diagrams for modelling and control of Dynamical Systems',

    long_description=long_description,
    long_description_content_type='text/markdown',

    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: Engineers',
        'Intended Audience :: Robotics',
        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3 :: Only'],

    project_urls={
        'Documentation': 'https://github.com/CallumJHays/bdsim_realtime',
        'Source': 'https://github.com/CallumJHays/bdsim_realtime',
        'Tracker': 'https://github.com/CallumJHays/bdsim_realtime/issues',
    },

    url='https://github.com/CallumJHays/bdsim_realtime',

    author='Callum Hays',

    author_email='callumjhays@gmail.com',

    keywords='python bdsim realtime control remote-control telemetry tuning-interface webapplication tuner signal-analysis control-system block-diagram computation-graph data-flow control-flow rtos simulation modeling computer-vision opencv',

    license='MIT',

    python_requires='>=3.6',

    packages=find_packages(exclude=["test_*", "TODO*"]),

    include_package_data=True,
    package_data={
        # TODO
        '': recursively_list_all_files('bdsim_realtime/webapp/client')
    },

    install_requires=['websockets', 'numpy', 'typing_extensions', 'sanic'],

    
    extras_require={
        'opencv': 'opencv-python' # if you want to use computer-vision blocks
    }

)

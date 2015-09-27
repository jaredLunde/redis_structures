#!/usr/bin/python3 -S
import os
import uuid
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


_dir = os.path.dirname(os.path.realpath(__file__))


def readme():
    with open(_dir + '/README.rst') as f:
        return f.read()

# parse_requirements() returns generator of pip.req.InstallRequirement objects
with open(_dir + '/requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='redis_structures',
    version='0.1.3',
    license='MIT',
    description='Redis data structures wrapped with Python 3.',
    long_description=readme(),
    author='Jared Lunde',
    author_email='jared.lunde@gmail.com',
    url='https://github.com/jaredlunde/redis_structures',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords=["redis", "data structures"],
    install_requires=required,
    packages=['redis_structures', 'redis_structures.debug'])

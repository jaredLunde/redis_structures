#!/usr/bin/python3 -S
import os
import uuid
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from pip.req import parse_requirements

def readme():
    with open('README.rst') as f:
        return f.read()

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements(
    os.path.dirname(os.path.realpath(__file__)) +
    "/requirements.txt",
    session=uuid.uuid1())

setup(
    name='redis_structures',
    version='0.1.1',
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
    install_requires=[str(ir.req) for ir in install_reqs],
    packages=['redis_structures', 'redis_structures.debug'])

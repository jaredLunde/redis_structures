#!/usr/bin/python3 -S
import os
import uuid
from distutils.core import setup
from pip.req import parse_requirements

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements(
    os.path.dirname(os.path.realpath(__file__))+\
    "/requirements.txt",
    session=uuid.uuid1())

# reqs is a list of requirement
reqs = [str(ir.req) for ir in install_reqs]
setup(
    name='redis_structures',
    version='0.0.1',
    description='Redis data structures wrapped with Python 3.',
    author='Jared Lunde',
    author_email='jared.lunde@gmail.com',
    url='https://github.com/jaredlunde/redis_structures',
    install_requires=reqs,
    packages=['redis_structures'])

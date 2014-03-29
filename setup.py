#!/usr/bin/env python

import multiprocessing
from setuptools import setup

setup(
    name="generators-to-coroutines",
    version="0.0.1",
    url="https://github.com/kholdstare/generators-to-coroutines",
    author="Alexander Kondratskiy",
    author_email="kholdstare0.0@gmail.com",
    description="Decorator for converting pull-based generators into push-based coroutines",
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License',
    ],
    packages=['generators_to_coroutines'],
    tests_require=['nose', 'nose-parameterized'],
    test_suite='nose.collector',
)

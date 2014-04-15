#!/usr/bin/env python

import multiprocessing
from setuptools import setup

setup(
    name="generators-to-coroutines",
    version="0.2.0",
    url="https://github.com/kholdstare/generators-to-coroutines",
    author="Alexander Kondratskiy",
    author_email="kholdstare0.0@gmail.com",
    description="Decorator for converting pull-based generators into push-based coroutines",
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'License :: OSI Approved :: BSD License',
    ],
    license='BSD',
    packages=['generators_to_coroutines'],
    tests_require=['nose', 'nose-parameterized'],
    test_suite='nose.collector',
)

#!/bin/bash

export PYTHONPATH=$(pwd)

nosetests -s -v ./tests/runtests.py

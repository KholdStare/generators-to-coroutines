#!/bin/bash

export PYTHONPATH=$(pwd)

nosetests -v ./tests/runtests.py

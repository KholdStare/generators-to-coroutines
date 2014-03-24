#!/usr/bin/env python

import unittest
import main
from codecorate import invertibleGenerator
from nose.tools import assert_equal
from nose_parameterized import parameterized


@invertibleGenerator(globals())
def genAfterLoop(iterable):

    for val in iterable:
        yield val

    yield 42


class DummyCoroutine(object):
    """ A dummy "sink" coroutine that records all values sent to it. """

    def __init__(self):
        self.results = []
        self.closed = False
        self.resultsAfterClose = []

    def send(self, val):
        if self.closed:
            self.resultsAfterClose.append(val)
        else:
            self.results.append(val)

    def close(self):
        self.closed = True


def runCoroutinePipeline(pipeline, iterable):

    dummy = DummyCoroutine()
    main.pushFromIterable(iterable, pipeline(dummy))

    return dummy.results


def runGeneratorPipeline(pipeline, iterable):

    return [val for val in pipeline(iterable)]


def assertEqualPipelines(genPipeline, coPipeline, iterable):

    cachedIterable = list(iterable)
    assert_equal(runCoroutinePipeline(coPipeline, cachedIterable),
                 runGeneratorPipeline(genPipeline, cachedIterable))


class TestEquivalence(unittest.TestCase):

    testParameters = [
        ("empty", []),
        ("one", [1]),
        ("odd list", [1, 2, 3, 4, 5]),
        ("even list", [1, 2, 3, 4, 5, 6]),
    ]

    @parameterized.expand(testParameters)
    def test_passthrough(self, _, l):
        assertEqualPipelines(
            main.genPassthrough, main.genPassthrough.co, l)

    @parameterized.expand(testParameters)
    def test_pair(self, _, l):
        assertEqualPipelines(
            main.genPairs,
            main.genPairs.co, l)

    @parameterized.expand(testParameters)
    def test_filter(self, _, l):
        iseven = lambda x: x % 2 == 0

        assertEqualPipelines(
            lambda i: main.genFilter(iseven, i),
            lambda i: main.genFilter.co(iseven, i),
            l)

    @parameterized.expand(testParameters)
    def test_after_loop(self, _, l):
        assertEqualPipelines(
            genAfterLoop,
            genAfterLoop.co, l)

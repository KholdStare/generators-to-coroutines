import unittest
from . import examples
from .decorators import invertibleGenerator, coroutine
from nose.tools import assert_equal
from nose_parameterized import parameterized


@invertibleGenerator(globals())
def genAfterLoop(iterable):

    for val in iterable:
        yield val

    yield 42


@invertibleGenerator(globals())
def genBeforeLoop(iterable):

    yield 42

    for val in iterable:
        yield val


@invertibleGenerator(globals())
def genTwoLoops(iterable):

    for val in iterable:
        if val == "break":
            yield "break from first"
            break
        yield "first: " + str(val)

    yield "between loops"

    for val in iterable:
        if val == "break":
            yield "break from second"
            break
        yield "second " + str(val)

    yield "done"


@coroutine
def coTwoLoops(target):
    notDone = True

    try:
        while notDone:
            val = (yield)
            if val == "break":
                target.send("break from first")
                break
            target.send("first: " + str(val))
    except GeneratorExit:
        notDone = False

    target.send("between loops")

    try:
        while notDone:
            val = (yield)
            if val == "break":
                target.send("break from second")
                break
            target.send("second " + str(val))
    except GeneratorExit:
        notDone = False

    target.send("done")


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
    examples.pushFromIterable(iterable, pipeline(dummy))

    return dummy.results


def runGeneratorPipeline(pipeline, iterable):
    results = [val for val in pipeline(iterable)]
    return results


def assertEqualPipelines(genPipeline, coPipeline, iterable):

    cachedIterable = list(iterable)
    assert_equal(runGeneratorPipeline(genPipeline, cachedIterable.__iter__()),
                 runCoroutinePipeline(coPipeline, cachedIterable))


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
            examples.genPassthrough, examples.genPassthrough.co, l)

    @parameterized.expand(testParameters)
    def test_pair(self, _, l):
        assertEqualPipelines(
            examples.genPairs,
            examples.genPairs.co, l)

    @parameterized.expand(testParameters)
    def test_filter(self, _, l):
        iseven = lambda x: x % 2 == 0

        assertEqualPipelines(
            lambda i: examples.genFilter(iseven, i),
            lambda i: examples.genFilter.co(iseven, i),
            l)

    @parameterized.expand(testParameters)
    def test_after_loop(self, _, l):
        assertEqualPipelines(
            genAfterLoop,
            genAfterLoop.co, l)

    @parameterized.expand(testParameters)
    def test_before_loop(self, _, l):
        assertEqualPipelines(
            genBeforeLoop,
            genBeforeLoop.co, l)

    @parameterized.expand(
        testParameters + [
            ("one break", ["break"]),
            ("val + one break", [1, "break"]),
            ("vals + one break", [1, 2, "break"]),
            ("one break + val", ["break", 1]),
            ("one break + vals", ["break", 1, 2]),
            ("two breaks", ["break", "break"]),
            ("vals + two breaks", [1, 2, "break", "break"]),
            ("two breaks + vals", ["break", "break", 1, 2]),
            ("break + vals + break", ["break", 1, 2, "break"]),
            ("vals + two break + vals", [1, 2, "break", 3, 4, "break", 5, 6]),
        ])
    def test_two_loops(self, _, l):
        assertEqualPipelines(
            genTwoLoops,
            genTwoLoops.co, l)

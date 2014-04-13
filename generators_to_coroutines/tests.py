from . import tools
from .decorators import hasInvertibleMethods, invertibleGenerator, coroutine

import unittest
import six
from nose.tools import assert_equal, raises
from nose_parameterized import parameterized


exampleGlobal = 42


def really():
    def deeply():

        @invertibleGenerator
        def nestedFunction(iterable):
            yield exampleGlobal

            for val in iterable:
                yield val

        return nestedFunction

    return deeply


@invertibleGenerator
def genAfterLoop(iterable):

    for val in iterable:
        yield val

    yield exampleGlobal


@invertibleGenerator
def genBeforeLoop(iterable):

    yield exampleGlobal

    for val in iterable:
        yield val


@invertibleGenerator
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


@invertibleGenerator
def genUsingNext(iterable):

    iterator = iterable.__iter__()

    try:
        while True:
            if six.PY3:
                yield iterator.__next__()
            else:
                yield iterator.next()
    except StopIteration:
        pass


@invertibleGenerator
def genUsingForAndNext(iterable):

    yield exampleGlobal

    iterator = iterable.__iter__()

    for val in iterator:
        if val % 2 == 0:
            yield val * 10
            if six.PY3:
                yield iterator.__next__()
            else:
                yield iterator.next()


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


@hasInvertibleMethods
class ClassWithGeneratorMethod(object):

    exampleClassLocal = 23

    def __init__(self, val):
        self.val = val

    def getGlobal(self):
        return exampleGlobal

    @invertibleGenerator
    def gen(self, iterable):

        yield self.val
        yield self.getGlobal()

        for elem in iterable:
            yield elem

        # TODO: limitation - cannot refer directly to ClassWithGeneratorMethod
        yield self.exampleClassLocal


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
    tools.pushFromIterable(iterable, pipeline(dummy))

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
            tools.genPassthrough, tools.genPassthrough.co, l)

    @parameterized.expand(testParameters)
    def test_pair(self, _, l):
        assertEqualPipelines(
            tools.genPairs,
            tools.genPairs.co, l)

    @parameterized.expand(testParameters)
    def test_filter(self, _, l):
        iseven = lambda x: x % 2 == 0

        assertEqualPipelines(
            lambda i: tools.genFilter(iseven, i),
            lambda i: tools.genFilter.co(iseven, i),
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

    @parameterized.expand(testParameters)
    def test_class_method(self, _, l):
        obj = ClassWithGeneratorMethod(7)
        assertEqualPipelines(
            obj.gen,
            obj.gen.co, l)

    @parameterized.expand(testParameters)
    def test_deep_nesting(self, _, l):
        func = really()()
        assertEqualPipelines(
            func,
            func.co, l)

    @raises(Exception)
    def test_cannot_convert_two_iterable_generator(self):
        def twoInput(in1, in2):
            for i1 in in1:
                yield i1

            for i2 in in2:
                yield i2

        invertibleGenerator(twoInput)

    @parameterized.expand(testParameters)
    def test_using_next(self, _, l):
        assertEqualPipelines(
            genUsingNext,
            genUsingNext.co, l)

    @parameterized.expand(testParameters)
    def test_using_for_and_next(self, _, l):
        assertEqualPipelines(
            genUsingForAndNext,
            genUsingForAndNext.co, l)

#!/usr/bin/env python

from .decorators import invertibleGenerator, coroutine


def pushFromIterable(iterable, target):

    try:
        for elem in iterable:
            target.send(elem)

        target.close()
    except StopIteration:
        pass


@invertibleGenerator
def genPairs(iterable):
    """ Aggregate two consecutive values into pairs """

    buf = []

    for elem in iterable:
        buf.append(elem)

        if len(buf) >= 2:
            yield tuple(buf)
            buf = []


@invertibleGenerator
def genFilter(predicate, iterable):
    """ Filter based on predicate """

    for elem in iterable:
        if predicate(elem):
            yield elem


@invertibleGenerator
def genPassthrough(iterable):
    """ Pass values through without modification """

    for val in iterable:
        yield val


@invertibleGenerator
def genMap(func, iterable):
    """ Map function on all values """

    for val in iterable:
        yield func(val)


@coroutine
def coSplit(predicate, trueTarget, falseTarget):

    while True:
        val = (yield)
        if predicate(val):
            trueTarget.send(val)
        else:
            falseTarget.send(val)

    trueTarget.close()
    falseTarget.close()


@coroutine
def coReceive():
    while True:
        val = (yield)
        print("Got %s" % str(val))


if __name__ == "__main__":

    text = """Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed
    diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat
    volutpat. Ut wisi enim ad minim veniam, quis nostrud exerci tation
    ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat. Duis
    autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie
    consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et
    accumsan et iusto odio dignissim qui blandit praesent luptatum zzril
    delenit augue duis dolore te feugait nulla facilisi. Nam liber tempor cum
    soluta nobis eleifend option congue nihil imperdiet doming id quod mazim"""

    words = text.split()

    predicate = lambda word: len(word) > 8

    print("Generators:")
    generatorPipeline = lambda words: genPairs(
        genMap(str.upper, genFilter(predicate, genPassthrough(words)))
    )

    for val in generatorPipeline(words):
        print("Got %s" % str(val))

    print("Coroutines:")
    coroutinePipeline = genPassthrough.co(
        genFilter.co(predicate,
        genMap.co(str.upper,
        genPairs.co(
        coReceive()
        ))))
    pushFromIterable(words, coroutinePipeline)

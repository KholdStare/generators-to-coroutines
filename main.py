#!/usr/bin/env python

from codecorate import (invertibleGenerator, coroutine)


def pushFromIterable(iterable, target):

    for elem in iterable:
        target.send(elem)

    target.close()


@invertibleGenerator(globals())
def genPairs(iterable):
    """ Aggregate two consecutive values into pairs """

    buf = []

    for elem in iterable:
        buf.append(elem)

        if len(buf) >= 2:
            yield tuple(buf)
            buf = []


@invertibleGenerator(globals())
def genFilter(predicate, iterable):
    """ Filter based on predicate """

    for elem in iterable:
        if predicate(elem):
            yield elem


@invertibleGenerator(globals())
def genPassthrough(iterable):
    """ Pass values through without modification """

    for val in iterable:
        yield val


@coroutine
def coReceive():
    while True:
        val = (yield)
        print "Got %s" % str(val)


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

    print "Generators:"
    for val in genPairs(genFilter(predicate, genPassthrough(words))):
        print "Got %s" % str(val)

    print "Coroutines:"
    pushFromIterable(words,
                     genPassthrough.co(
                     genFilter.co(predicate,
                     genPairs.co(
                     coReceive()
                     ))))

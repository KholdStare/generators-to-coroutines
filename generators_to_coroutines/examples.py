#!/usr/bin/env python

from .decorators import coroutine
from .tools import genPassthrough, genFilter, genMap, genPairs,\
    coReceive, pushFromIterable


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

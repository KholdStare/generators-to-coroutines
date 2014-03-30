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

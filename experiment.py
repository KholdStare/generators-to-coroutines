#!/usr/bin/env python

from codecorate import *

######
# Coroutine stuff

@coroutine
def coFilter(target):
    buf = []

    while True:
        elem = (yield)
        buf.append(elem)

        if len(buf) >= 2:
            target.send(buf)
            buf = []

# is currying necessary?
def sourceFromIterable(iterable):

    def source(target):
        for elem in iterable:
            target.send(elem)

        target.close()

    return source


#####
# Gen stuff

@invertibleGenerator
def genFilter(iterable):
    
    buf = []

    for elem in iterable:
        buf.append(elem)

        if len(buf) >= 2:
            yield buf
            buf = []

@coroutine
def receiver():
    print("Ready to receive")
    while True:
        n = (yield)
        print("Got %s" % n)

@invertibleGenerator
def simpleGen(iterable):
    for val in iterable:
        yield val

@coroutine
def simpleCo(target):
    while True:
        val = (yield)
        target.send(val)

if __name__ == "__main__":
    
    sourceFromIterable(xrange(0,9))(genFilter.co(
                                    simpleGen.co(
                                    receiver())))



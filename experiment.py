#!/usr/bin/env python

import dis

######
# Coroutine stuff

def coroutine(func):
    def start(*args, **kwargs):
        g = func(*args, **kwargs)
        g.next()
        return g
    return start

@coroutine
def co_filter(target):
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

def generatorToCoroutine(func):

    def start(target):

        g = func(*args, **kwargs)
        g.next()
        return g
    return start

class CoGenWrapper(object):

    class IterableProxy(object):

        def __init__(self, parentWrapper):
            pass


    def __init__(self, target):
        pass


def gen_filter(iterable):
    
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

def simpleGen(iterable):
    for val in iterable:
        yield val

def simpleCo(target):
    while True:
        val = (yield)
        target.send(val)

if __name__ == "__main__":

    print "Generator:"
    dis.dis(simpleGen)
    print "Coroutine:"
    dis.dis(simpleCo)
    print "Bigger Generator:"
    dis.dis(gen_filter)
    
    sourceFromIterable(xrange(0,9))(co_filter(
                                    receiver()))



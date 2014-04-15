# Turn your generators into coroutines!

[![Build Status](https://travis-ci.org/KholdStare/generators-to-coroutines.svg?branch=master)](https://travis-ci.org/KholdStare/generators-to-coroutines?branch=master)
[![PyPI version](https://badge.fury.io/py/generators-to-coroutines.png)](http://badge.fury.io/py/generators-to-coroutines)

## TL;DR

* `pip install generators-to-coroutines`
* Use the `invertibleGenerator` decorator, to automatically create an
  equivalent push-based coroutine from a pull-based generator.
* Access this coroutine through the `co` member.
* Reuse all your existing generators in [coroutine pipelines][cocourse].
* Use with python 2.6, 2.7, 3.2, 3.3, or pypy.
* The `iterable` parameter to the generator that was pulled from, now becomes the
  `target` parameter of the coroutine that is pushed to.

```
from generators_to_coroutines import invertibleGenerator

@invertibleGenerator
def genMap(func, iterable):
    """ Map function on all values """

    for val in iterable:
        yield func(val)

generatorPipeline = \
    lambda iterable: genFilter(predicate, genMap(str.upper, iterable))

coroutinePipeline = \
    lambda target: genMap.co(str.upper, genFilter.co(predicate, target))
```

## Motivation

Python has a lot of support for iterator based pipelines. In particular,
support for generators and the `itertools` module make building functional
data-processing pipelines a breeze.

    def genFilter(predicate, iterable):
        """ Filter based on predicate. Equivalent to ifilter in itertools """

        for elem in iterable:
            if predicate(elem):
                yield elem

Pull-based (iterator) pipelines are great for linear sequences of
transformations. However, when a stream of data/events needs to be processed in
several different ways, there is no easy way to split a pull-based pipeline,
without going over an iterable more than once.

An excellent solution to this problem are [push-based pipelines that use
coroutines][cocourse]. An equivalent filter coroutine that can be integrated
into such a pipeline looks very similar to the generator:

    @coroutine
    def coFilter(predicate, target):
        """ Filter based on predicate """

        while True:
            elem = (yield)
            if predicate(elem):
                target.send(elem)

It would be a shame to have to rewrite all your existing generators to
equivalent coroutines...  Luckily the transformation is fairly mechanical, and
can be done by manipulating the AST of the generator, with the
`invertibleGenerator` decorator!

    from generators_to_coroutines import invertibleGenerator

    @invertibleGenerator
    def genMap(func, iterable):
        """ Map function on all values """

        for val in iterable:
            yield func(val)

## Limitations

This package is very much experimental and a proof of concept! A lot more could
be done.

Conversion is currently best-effort - some more complex generators will be
converted to coroutines with a slightly different exit point - mainly due to
different behaviour between `StopIteration` and `GeneratorExit`. Some obvious
cases that cannot be converted will result in an `Exception` during conversion.
It would be beneficial to raise an `Exception` in all cases where the
conversion isn't guaranteed to be perfect.

[cocourse]: http://www.dabeaz.com/coroutines/

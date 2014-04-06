from .ast_transformers import InvertGenerator, transformAstWith
from .descriptor_magic import \
    wrapMethodAndAttachDescriptors, BindingExtensionDescriptor
import six
import inspect


def coroutine(func):
    def start(*args, **kwargs):
        g = func(*args, **kwargs)
        six.next(g)
        return g
    return start


def _funcIsMethod(stackFromFunc):
    """ Determine whether a function being decorated is actually a method of a
    class, given the stack frames above the decorator invocation. """
    funcFrame = stackFromFunc[0]
    potentialClassName = funcFrame[3]

    nextFrame = stackFromFunc[1]
    return nextFrame[3] == '<module>' and \
        nextFrame[4][0].startswith('class ' + potentialClassName)


def hasInvertibleMethods(cls):
    """ Class decorator that transforms methods that have been marked with
    "invertibleGenerator" """

    #frames = inspect.stack()

    #from pprint import PrettyPrinter
    #globs = map(lambda frame: frame[0].f_globals, frames)
    #locs = map(lambda frame: frame[0].f_locals, frames)

    #pp = PrettyPrinter(indent=4)
    #for (glob, loc) in zip(globs, locs):
        #print "GLOBALS:"
        #pp.pprint(glob)
        #print "LOCALS:"
        #pp.pprint(loc)

    for name, method in six.iteritems(cls.__dict__):
        if hasattr(method, "markForConversion"):
            # TODO: transform and wrap
            # But need globals/locals
            pass
    return cls


def _makeInvertibleUsingFrame(frame, func):
    """ Add a co method to a generator function, that is the equivalent
    coroutine. """

    return coroutine(
        transformAstWith(
            frame[0].f_globals,
            frame[0].f_locals,
            [InvertGenerator])(func)
    )


def invertibleGenerator(func):
    """ Add a co method to a generator function, that is the equivalent
    coroutine. """

    frames = inspect.stack()
    nextFrame = frames[1]

    transformedFunc = _makeInvertibleUsingFrame(nextFrame, func)

    if _funcIsMethod(frames[1:]):
        # TODO: either remove, or use in class decorator
        func.markForConversion = True

        return wrapMethodAndAttachDescriptors({
            'co': BindingExtensionDescriptor(transformedFunc)
        })(func)
    else:
        func.co = transformedFunc
        return func

from .ast_transformers import InvertGenerator, transformAstWith
import six
import inspect


def coroutine(func):
    def start(*args, **kwargs):
        g = func(*args, **kwargs)
        six.next(g)
        return g
    return start


def invertibleGenerator(func):
    """ Add a co method to a generator function, that is the equivalent
    coroutine. """

    globalEnv = inspect.stack()[1][0].f_globals

    func.co = coroutine(
        transformAstWith(globalEnv, [InvertGenerator])(func)
    )
    return func

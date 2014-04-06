import copy
import six


class BindingExtensionDescriptor(object):
    """ Descriptor for a function that can be attached to a bound method,
    and become bound to the same object instance.

    For example:

        obj.method.extended(*args)

    extended(*args) would be called called with obj as an implicit parameter,
    i.e.  'extended' would be a bound method if it was attached using this
    descriptor.

    The attaching process is complicated... (see other functions/classes in
    this module.)"""

    def __init__(self, func):
        self.func = func

    def __get__(self, boundMethod, type=None):
        obj = boundMethod.__self__
        return six.create_bound_method(self.func, obj)


def wrapMethodAndAttachDescriptors(descriptors):
    """ Given a dictionary mapping names to descriptor objects, create a
    decorator for attaching these descriptors to a bound method. """

    class WrapMethod(object):
        """ A descriptor that wraps a method, and intercepts calls to __get__,
        to inject other descriptors onto instances of the bound method. """

        def __init__(self, func):
            self.func = func
            self.descriptors = descriptors

        def __get__(self, obj, type=None):
            method = six.create_bound_method(self.func, obj)
            if obj is not None:
                return _wrapAlreadyBoundMethodAndAttachDescriptors(
                    method, self.descriptors)
            return method

    return WrapMethod


class BoundMethodWrapper(object):
    """ Wraps a bound method in an object, to allow invoking of descriptors on
    said method. """

    def __init__(self, boundMethod):
        self.boundMethod = boundMethod

    def __call__(self, *args, **kwargs):
        return self.boundMethod(*args, **kwargs)

    def __getattr__(self, attr):
        return self.boundMethod.__getattribute__(attr)


def _wrapAlreadyBoundMethodAndAttachDescriptors(boundMethod, descriptors):
    """ Given a bound method and descriptors, wrap the method appropriately so
    the descriptors are properly attached and invoked. """

    # need a specialized copy of the wrapping class to attach these
    # descriptors
    localBoundMethodWrapperClass = copy.copy(BoundMethodWrapper)

    for key in descriptors:
        setattr(localBoundMethodWrapperClass, key, descriptors[key])

    return localBoundMethodWrapperClass(boundMethod)

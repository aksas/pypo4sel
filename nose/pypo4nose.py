from nose.plugins import Plugin

from pypo4sel.core import log2l


# noinspection PyPep8Naming,PyProtectedMember
class PypoNose(Plugin):
    name = 'pyponose'

    def __init__(self):
        super(PypoNose, self).__init__()
        self._stack = []

    def begin(self):
        id_ = log2l._notify_start(suit=dict(name='Global'))
        self._stack.append(id_)

    def addError(self, test, err):
        log2l._notify_exception(self._stack[-1], err, test=test)

    def addFailure(self, test, err):
        log2l._notify_exception(self._stack[-1], err, test=test)

    def addSkip(self, test):
        log2l._notify_exception(self._stack[-1], "skip", test=test)

    def beforeTest(self, test):
        if hasattr(test.test, "test"):
            method = test.test.test
        else:
            # noinspection PyProtectedMember
            method = getattr(test.test, test.test._testMethodName)
        hierarchy = ".".join(test.address()[1:])

        id_ = log2l._notify_start(test=dict(test=test, hierarchy=hierarchy, method=method))
        self._stack.append(id_)

    def afterTest(self, test):
        log2l._notify_end(self._stack.pop(), test=test)

    def startContext(self, context):
        name = context.__name__
        if hasattr(context, '__module__'):
            name = context.__module__ + '.' + name
        id_ = log2l._notify_start(suit=dict(name=name, doc=context.__doc__, context=context))
        self._stack.append(id_)

    def stopContext(self, context):
        log2l._notify_end(self._stack.pop(), suit=context)

    def finalize(self, res):
        log2l._notify_end(self._stack.pop(), suit='END', res=res)

import traceback
from unittest import SkipTest

from allure.common import AllureImpl
from allure.constants import Status, Label, AttachmentType, Severity
from allure.structure import TestLabel, TestStep
from nose.plugins import Plugin
from nose.plugins.attrib import attr
from pypo4sel.core import log2l
from pypo4sel.core.log2l import Options, ListenerMixin


# noinspection PyPep8Naming
class PypoNose(Plugin):
    name = 'pyponose'

    def __init__(self):
        super(PypoNose, self).__init__()
        self._stack = []
        log2l.listeners.append(AllureLogger("test_report"))

    def begin(self):
        id_ = log2l._notify_start()
        self._stack.append(id_)

    def addError(self, test, err):
        log2l._notify_exception(self._stack[-1], *err, test=test)

    def addFailure(self, test, err):
        log2l._notify_exception(self._stack[-1], *err, test=test)

    def addSkip(self, test):
        pass

    def beforeTest(self, test):
        id_ = log2l._notify_start(test=test)
        self._stack.append(id_)

    def afterTest(self, test):
        log2l._notify_end(self._stack.pop(), test=test)

    def startContext(self, context):
        id_ = log2l._notify_start(suit=context)
        self._stack.append(id_)

    def stopContext(self, context):
        log2l._notify_end(self._stack.pop(), suit=context)

    def finalize(self, res):
        log2l._notify_end(self._stack.pop(), res=res)


# # wrappers for allure


def attach(name, contents, attach_type=AttachmentType.TEXT):
    log2l.message(name, attach=dict(contents=contents, type=attach_type))


def label(name, value):
    return attr(**{'%s_%s' % (Label.DEFAULT, name): value})


def severity(s):
    return label(Label.SEVERITY, s)


def feature(f):
    return label(Label.FEATURE, f)


def story(s):
    return label(Label.STORY, s)


def issue(i):
    return label(Label.ISSUE, i)


def severity_level():
    return Severity


class AllureLoggerI(ListenerMixin):
    def __init__(self, log_dir):
        self.impl = AllureImpl(log_dir)
        self.store = {}
        self.suppress = None
        self.error = None
        self.precondition_steps = False
        self.suits = []

    def _before(self):
        if self.precondition_steps:
            self._stop_test()
            self.precondition_steps = False
        self.error = None
        self.suppress = None

    def _start_context(self, name, doc):
        self._before()
        self.impl.start_suite(name, doc)
        self.suits.append(self.impl.testsuite)

    def _stop_context(self):
        if self.precondition_steps:
            self.precondition_steps = False
        if self.impl.testsuite and self.impl.testsuite.tests:
            self.impl.stop_suite()
        if len(self.suits) > 1:
            self.suits.pop()
            self.impl.testsuite = self.suits[-1]
        else:
            self.impl.testsuite = None
            self.suits = []

    def _start_test(self, test):
        self._before()
        if hasattr(test.test, "test"):
            method = test.test.test
        else:
            method = getattr(test.test, test.test._testMethodName)
        hierarchy = ".".join(test.address()[1:])
        self.impl.start_case(hierarchy, description=method.__doc__, labels=get_labels(method))

    def _stop_test(self):
        if self.error:
            self.impl.stop_case(**self.error)
            if self.precondition_steps:
                self._stop_context()
        else:
            self.impl.stop_case(Status.PASSED)
        self.impl.stack.pop()
        self.error = None
        self.suppress = None

    def _test_step(self, options):
        if Options.STEP_MESSAGE in options:
            message = options[Options.STEP_MESSAGE].format(**options)
        elif Options.ELEMENT_NAME in options:
            params = str(options[Options.ARGS][1:]) if len(options[Options.ARGS]) > 1 else ""
            params += str(options[Options.KWARGS]) if len(options[Options.KWARGS]) > 0 else ""
            message = "on {} do {} with {}" if params else "on {} do {}"
            message = message.format(options[Options.ARGS][0].name, options[Options.STEP_NAME], params)
        else:
            message = options[Options.STEP_NAME]
        return self.impl.start_step(message)

    def start_step(self, step_id, **options):
        if not options:
            self._start_context('Global', None)
            self.store[step_id] = 'START'
        elif 'suit' in options:
            suit = options['suit']
            name = suit.__name__
            if hasattr(suit, '__module__'):
                name = suit.__module__ + '.' + name
            self._start_context(name, suit.__doc__)
            self.store[step_id] = 'SUIT'
        elif 'test' in options:
            self._start_test(options['test'])
            self.store[step_id] = 'TEST'
        elif self.suppress is None:
            self.suppress = step_id if options.get(Options.SUPPRESS_CHILD_LOGS, False) else None
            self.store[step_id] = self._test_step(options)
        else:
            self.store[step_id] = 'suppressed'

    def end_step(self, step_id, **kwargs):
        t = self.store.pop(step_id)
        if t == 'START':
            self._stop_context()
            self.impl.store_environment()
        elif t == 'SUIT':
            self._stop_context()
        elif t == 'TEST':
            self._stop_test()
        elif isinstance(t, TestStep):
            if self.error:
                t.status = self.error['status']
            else:
                t.status = Status.PASSED
            self.impl.stop_step()

    def exception(self, step_id, exc_type, exc_val, exc_tb):
        if self.error is None and exc_type is not None:
            failure = getattr(self.store[step_id], 'failureException', AssertionError)
            if exc_type == SkipTest:
                status = Status.CANCELED
            elif exc_type == failure:
                status = Status.FAILED
            else:
                status = Status.BROKEN
            message = ''.join(traceback.format_exception_only(exc_type, exc_val)).strip()
            trace = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb)).strip()
            self.error = dict(status=status, message=message, trace=trace)

    def message(self, msg, **kwargs):
        if not self.impl.stack:
            self.impl.start_case(self.impl.testsuite.name + ".Preconditions")
            self.precondition_steps = True
        if 'attach' in kwargs:
            self.impl.attach(msg, kwargs['attach']['contents'], kwargs['attach']['type'])
        else:
            if 'details' in kwargs:
                self.impl.attach(msg, kwargs['details'], AttachmentType.TEXT)
            else:
                self.impl.start_step(msg)
                self.impl.stop_step()


def get_labels(test):
    def get_markers(item, name):
        markers = []

        for prop in dir(item):
            if prop.startswith(Label.DEFAULT):
                key = prop.split('_')[-1]
                value = getattr(item, prop)
                markers.append((key, value))

        return markers

    labels = []
    label_markers = get_markers(test, Label.DEFAULT)
    for name, value in label_markers:
        labels.append(TestLabel(name=name, value=value))

    return labels


class AllureLogger(ListenerMixin):
    def __init__(self, log_dir):
        self.preconditions = False
        self.suppress = None
        self.error = None
        self.suits = []
        self.impl = AllureImpl(log_dir)

    def start_step(self, step_id, **options):
        super(AllureLogger, self).start_step(step_id, **options)

    def end_step(self, step_id, **options):
        super(AllureLogger, self).end_step(step_id, **options)

    def message(self, msg, **kwargs):
        if not self.impl.stack:  # there are no current tests
            self.suppress = None
            self.error = None
            self.impl.start_case(self.impl.testsuite.name + ".Preconditions")
            # TODO handle teardown actions
            self.preconditions = True
        if 'attach' in kwargs:
            self.impl.attach(msg, kwargs['attach']['contents'], kwargs['attach']['type'])
        else:
            if 'details' in kwargs:
                self.impl.attach(msg, kwargs['details'], AttachmentType.TEXT)
            else:
                self.impl.start_step(msg)
                self.impl.stop_step()

    def exception(self, step_id, err, **options):
        exc_type, exc_val, exc_tb = err
        if self.error is None and exc_type is not None:
            failure = getattr(self.store[step_id], 'failureException', AssertionError)
            if exc_type == SkipTest:
                status = Status.CANCELED
            elif exc_type == failure:
                status = Status.FAILED
            else:
                status = Status.BROKEN
            message = ''.join(traceback.format_exception_only(exc_type, exc_val)).strip()
            trace = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb)).strip()
            self.error = dict(status=status, message=message, trace=trace)

    def _store_test(self):
        if self.error:
            self.impl.stop_case(**self.error)
        else:
            self.impl.stop_case(Status.PASSED)
        self.impl.stack.pop()

    def _start_test(self, test):
        if self.preconditions:
            self._store_test()
            self.preconditions = False
        if hasattr(test.test, "test"):
            method = test.test.test
        else:
            method = getattr(test.test, test.test._testMethodName)
        self.suppress = None
        self.error = None
        hierarchy = ".".join(test.address()[1:])
        self.impl.start_case(hierarchy, description=method.__doc__, labels=get_labels(method))

    def _store_context(self):
        if self.impl.testsuite and self.impl.testsuite.tests:
            self.impl.stop_suite()
        if len(self.suits) > 1:
            self.suits.pop()
            self.impl.testsuite = self.suits[-1]
        else:
            self.impl.testsuite = None
            self.suits = []

    def _start_context(self, name, doc):
        if self.preconditions and self.error:
            self._store_test()
            self._store_context()
            self.preconditions = False
        self.impl.start_suite(name, doc)
        self.suits.append(self.impl.testsuite)

    def _end_context(self, context):
        if self.preconditions:
            self._store_test()
            self.preconditions = False
        # TODO handle `another context end after error
        self._store_context()
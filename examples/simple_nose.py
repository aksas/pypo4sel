import traceback

import sys
from allure.common import AllureImpl
from allure.constants import Status, Label, AttachmentType, Severity, ALLURE_NAMESPACE
from allure.rules import xmlfied, Element, Nested, WrappedMany, Attribute, Rule, element_maker, legalize_xml
from allure.structure import TestLabel
from allure.utils import unicodify, now
from nose.plugins import Plugin
from nose.plugins.attrib import attr

from pypo4sel.core import log2l
from pypo4sel.core.log2l import Options, ListenerMixin


# noinspection PyPep8Naming,PyProtectedMember
class PypoNose(Plugin):
    name = 'pyponose'

    def __init__(self):
        super(PypoNose, self).__init__()
        self._stack = []
        log2l.listeners.append(AllureLogger("test_report"))

    def begin(self):
        id_ = log2l._notify_start(suit='BEGIN')
        self._stack.append(id_)

    def addError(self, test, err):
        log2l._notify_exception(self._stack[-1], err, test=test)

    def addFailure(self, test, err):
        log2l._notify_exception(self._stack[-1], err, test=test)

    def addSkip(self, test):
        log2l._notify_exception(self._stack[-1], "skip", test=test)

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


def get_labels(test):
    def get_markers(item):
        markers = []

        for prop in dir(item):
            if prop.startswith(Label.DEFAULT):
                key = prop.split('_')[-1]
                v = getattr(item, prop)
                markers.append((key, v))

        return markers

    labels = []
    label_markers = get_markers(test)
    for name, value in label_markers:
        labels.append(TestLabel(name=name, value=value))

    return labels


class Description(Element):
    def value(self, name, what):
        if isinstance(what, tuple):
            val = legalize_xml(unicodify(what[1]))
            tp = what[0]
        else:
            val = legalize_xml(unicodify(what))
            tp = 'text'
        return element_maker(self.name or name, self.namespace)(val, type=tp)

TestCase = xmlfied('test-case',
                   name=Element(),
                   title=Element().if_(lambda x: x),
                   description=Description().if_(lambda x: x),
                   failure=Nested().if_(lambda x: x),
                   steps=WrappedMany(Nested()),
                   attachments=WrappedMany(Nested()),
                   labels=WrappedMany(Nested()),
                   status=Attribute(),
                   start=Attribute(),
                   stop=Attribute())


TestSuite = xmlfied('test-suite',
                    namespace=ALLURE_NAMESPACE,
                    name=Element(),
                    title=Element().if_(lambda x: x),
                    description=Description().if_(lambda x: x),
                    tests=WrappedMany(Nested(), name='test-cases'),
                    labels=WrappedMany(Nested()),
                    start=Attribute(),
                    stop=Attribute())


class AllureLogger(ListenerMixin):
    def __init__(self, log_dir):
        self.preconditions = False
        self.suppress = None
        self.error = None
        self.suits = []
        self.impl = AllureImpl(log_dir)

    def start_step(self, step_id, **options):
        if 'suit' in options:
            suit = options['suit']
            if suit == 'BEGIN':
                self._start_context('Global', None)
            else:
                name = suit.__name__
                if hasattr(suit, '__module__'):
                    name = suit.__module__ + '.' + name
                self._start_context(name, suit.__doc__)
        elif 'test' in options:
            self._start_test(options['test'])
        elif self.suppress is None:
            self.suppress = step_id if options.get(Options.SUPPRESS_CHILD_LOGS, False) else None
            self._test_step(options)

    def end_step(self, step_id, **options):
        if 'res' in options:
            self._end_context()
            self.impl.store_environment()
        elif 'suit' in options:
            self._end_context()
        elif 'test' in options:
            self._store_test()
        else:
            if step_id == self.suppress:
                self.suppress = None
            if self.suppress is None:
                if self.error:
                    self.impl.stack[-1].status = self.error['status']
                else:
                    self.impl.stack[-1].status = Status.PASSED
                self.impl.stop_step()

    def message(self, msg, **kwargs):
        if self.suppress is None:
            self._check_test_started()
            if 'attach' in kwargs:
                self.impl.attach(msg, kwargs['attach']['contents'], kwargs['attach']['type'])
            else:
                if 'details' in kwargs:
                    self.impl.attach(msg, kwargs['details'], AttachmentType.TEXT)
                else:
                    self.impl.start_step(msg)
                    self.impl.stop_step()

    def exception(self, step_id, err, **options):
        if err == 'skip':
            self.error = dict(status=Status.CANCELED, message=None, trace=None)
        elif self.error is None:
            exc_type, exc_val, exc_tb = err
            failure = getattr(options.get('test', ''), 'failureException', AssertionError)
            if exc_type == failure:
                status = Status.FAILED
            else:
                status = Status.BROKEN
            message = ''.join(traceback.format_exception_only(exc_type, exc_val)).strip()
            trace = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb)).strip()
            self.error = dict(status=status, message=message, trace=trace)

    def _check_test_started(self):
        if not self.impl.stack:  # there are no current tests
            self.suppress = None
            self.error = None
            if self.impl.testsuite.tests:
                self._start_case(self.impl.testsuite.name + ".TearDown")
            else:
                self._start_case(self.impl.testsuite.name + ".Preconditions")
            self.preconditions = True

    def _test_step(self, options):
        self._check_test_started()
        if Options.STEP_MESSAGE in options:
            message = options[Options.STEP_MESSAGE].format(**options)
        elif Options.ELEMENT_NAME in options:
            params = str(options[Options.ARGS][1:]) if len(options[Options.ARGS]) > 1 else ""
            params += str(options[Options.KWARGS]) if len(options[Options.KWARGS]) > 0 else ""
            message = "{} of {} perform {} with {}" if params else "{} of {} perform {}"
            # noinspection PyProtectedMember
            message = message.format(options[Options.ARGS][0].name,
                                     options[Options.ARGS][0]._owner.name,
                                     options[Options.STEP_NAME], params)
        else:
            message = options[Options.STEP_NAME]
        return self.impl.start_step(message)

    def _store_test(self):
        if self.error:
            self.impl.stop_case(**self.error)
        else:
            self.impl.stop_case(Status.PASSED)
        self.impl.stack.pop()

    def _start_test(self, test):
        self.suppress = None
        self.error = None
        if self.preconditions:
            self._store_test()
            self.preconditions = False
        if hasattr(test.test, "test"):
            method = test.test.test
        else:
            # noinspection PyProtectedMember
            method = getattr(test.test, test.test._testMethodName)
        hierarchy = ".".join(test.address()[1:])
        self._start_case(hierarchy, description=method.__doc__, labels=get_labels(method))

    def _start_case(self, name, description=None, labels=None):
        if description:
            description = ('markdown', cleandoc(description))
        test = TestCase(name=name,
                        description=description,
                        start=now(),
                        attachments=[],
                        labels=labels or [],
                        steps=[])
        self.impl.stack.append(test)

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
        if self.preconditions:
            # setup of previous suit
            self._store_test()
            if self.error:
                # fails
                self._store_context()
            self.preconditions = False
        self._start_suite(name, doc)
        self.suits.append(self.impl.testsuite)

    def _end_context(self):
        if self.preconditions:
            # tear down actions
            self._store_test()
            if self.error:
                # fails in nested suit
                self._store_context()
            self.preconditions = False
        self._store_context()

    def _start_suite(self, name, description=None, title=None, labels=None):
        if description:
            description = ('markdown', cleandoc(description))
        self.impl.testsuite = TestSuite(name=name,
                                        title=title,
                                        description=description,
                                        tests=[],
                                        labels=labels or [],
                                        start=now())


def cleandoc(doc):
    if doc:
        lines = doc.expandtabs().splitlines()
        margin = sys.maxint
        for line in lines[1:]:
            content = len(line.lstrip())
            if content:
                margin = min(margin, len(line) - content)
        trimmed = [lines[0].strip()]
        if margin < sys.maxint:
            for line in lines[1:]:
                trimmed.append(line[margin:])

        while trimmed and not trimmed[-1]:
            trimmed.pop()
        while trimmed and not trimmed[0]:
            trimmed.pop(0)
        return '\n'.join(trimmed)
    return doc

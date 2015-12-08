import sys
import traceback

from allure.common import AllureImpl
from allure.constants import AttachmentType, ALLURE_NAMESPACE, Status, Label
from allure.rules import Element, legalize_xml, element_maker, xmlfied, Nested, WrappedMany, Attribute
from allure.structure import TestLabel
from allure.utils import unicodify, now

from pypo4sel.core.log2l import Options


class AllureLogger(object):
    def __init__(self, log_dir, error_formatter=default_format_error, doc_type=None):
        self.preconditions = False
        self.suppress = None
        self.error = None
        self.suits = []
        self.impl = AllureImpl(log_dir)
        self.error_formatter = error_formatter
        self.doc_type = doc_type

    def start_step(self, step_id, **options):
        if 'suit' in options:
            self._start_context(options['suit'])
        elif 'test' in options:
            self._start_test(options['test'])
        elif self.suppress is None:
            self.suppress = step_id if options.get(Options.SUPPRESS_CHILD_LOGS, False) else None
            self._test_step(options)

    def end_step(self, step_id, **options):
        if 'suit' in options:
            self._end_context()
            if options['suit'] == 'END':
                self.impl.store_environment()
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
                attach = kwargs['attach']
                attach_type = AttachmentType.TEXT
                if 'attach_type' in attach['kwargs']:
                    attach_type = attach['kwargs']['attach_type']
                elif attach['args']:
                    attach_type = attach['args'][0]
                self.impl.attach(msg, attach['contents'], attach_type)
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
            self.error = self.error_formatter(step_id, err, **options)

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
        method = test.get('method')
        self._start_case(test['hierarchy'], description=method.__doc__, labels=get_labels(method))

    def _start_case(self, name, description=None, labels=None):
        if description and self.doc_type:
            description = (self.doc_type, cleandoc(description))
        test = TestCase(name=name,
                        description=description,
                        start=now(),
                        attachments=[],
                        labels=labels or [],
                        steps=[])
        self.impl.stack.append(test)

    def _store_context(self):
        # TODO and handling for parent suit level documentation
        if self.impl.testsuite and self.impl.testsuite.tests:
            self.impl.stop_suite()
        if len(self.suits) > 1:
            self.suits.pop()
            self.impl.testsuite = self.suits[-1]
        else:
            self.impl.testsuite = None
            self.suits = []

    def _start_context(self, context):
        if self.preconditions:
            # setup of previous suit
            self._store_test()
            if self.error:
                # fails
                self._store_context()
            self.preconditions = False
        self._start_suite(context["name"], context.get("doc"))
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
        if description and self.doc_type:
            description = (self.doc_type, cleandoc(description))
        self.impl.testsuite = TestSuite(name=name,
                                        title=title,
                                        description=description,
                                        tests=[],
                                        labels=labels or [],
                                        start=now())


# noinspection PyUnusedLocal
def default_format_error(step_id, err, **options):
    exc_type, exc_val, exc_tb = err
    if exc_type == AssertionError:
        status = Status.FAILED
    else:
        status = Status.BROKEN
    message = ''.join(traceback.format_exception_only(exc_type, exc_val)).strip()
    trace = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb)).strip()
    return dict(status=status, message=message, trace=trace)


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

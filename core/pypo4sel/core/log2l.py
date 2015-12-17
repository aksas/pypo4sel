"""

class Element(PageElement):

    @logging.step
    def method(self, *fargs, **fkwargs):
        do_smth_here

class Page(object):
    my_element = Element('#id')


each time when 'method' will be called the 'start_step' will be called with the following 'options':
 {
    'element_name':'my_element',
    'step_name':'method',
    'args':<fargs>,
    'kwargs':<fkwargs>
 }

if step wrapper will be used like this:
    @logging.step("any text")
    def method(self, *fargs, **fkwargs):

then 'options' parameter of 'start_step' will look like:
 {
    'first_param':'any text'
    'element_name':'my_element',
    'step_name':'method',
    'args':<fargs>,
    'kwargs':<fkwargs>
 }

for example, it may be used for specifying of custom log message format, like
    @logging.step("{step_name} of {my_element} was called")
    def method(self, *fargs, **fkwargs):
        ...

    class MyL(ListenerMixin):
        def start_step(self, step_id, options)
            if 'first_param' in options:
                print options['first_param'].format(**options)
            else:
                print '{my_element}.{step_name}({args}, {fkwargs})'.format(**options)
"""

import functools
import sys
import uuid

__All__ = ["step", "listeners", "message", "action", "debug"]


class Options(object):
    STEP_MESSAGE = "first_param"
    STEP_NAME = "step_name"
    ELEMENT_NAME = "element_name"
    KWARGS = "kwargs"
    ARGS = "args"
    SUPPRESS_CHILD_LOGS = "suppress_child_logs"
    DEBUG_MESSAGE = "debug_message"


class ListenerMixin(object):
    def start_step(self, step_id, **options):
        pass

    def end_step(self, step_id, **options):
        pass

    def exception(self, step_id, err, **options):
        pass

    def message(self, msg, **kwargs):
        pass


listeners = []
""" :type: list[ListenerMixin] """


# noinspection PyPep8Naming
class step(object):
    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            return _decorator(args[0], {})
        return super(step, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            raise Exception("Only one unnamed parameter is allowed.")
        self.options = kwargs
        if len(args) == 1:
            self.options[Options.STEP_MESSAGE] = args[0]

    def __call__(self, method):
        return _decorator(method, self.options)

    def __enter__(self):
        assert Options.STEP_MESSAGE in self.options
        self.step_id = _notify_start(**self.options)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            _notify_exception(self.step_id, (exc_type, exc_val, exc_tb))
        _notify_end(self.step_id)


# noinspection PyPep8Naming
class action(step):
    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            return _decorator(args[0], {Options.SUPPRESS_CHILD_LOGS: True})
        return super(step, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        super(action, self).__init__(*args, **kwargs)
        self.options[Options.SUPPRESS_CHILD_LOGS] = True


def debug(msg, **kwargs):
    kwargs.update({Options.DEBUG_MESSAGE: True})
    message(msg, **kwargs)


def attach(msg, contents, *args, **kwargs):
    message(msg, attach=dict(contents=contents, args=args, kwargs=kwargs))


def message(msg, **kwargs):
    [l.message(msg, **kwargs) for l in listeners]


def _decorator(method, step_options):
    step_options.setdefault(Options.STEP_NAME, method.func_name)

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        options = step_options.copy()
        fargs = args
        if len(args) > 0 and hasattr(args[0], "_name"):
            # noinspection PyProtectedMember
            options.setdefault(Options.ELEMENT_NAME, args[0]._name)
        options.setdefault(Options.KWARGS, kwargs)
        options.setdefault(Options.ARGS, args)
        step_id = _notify_start(**options)
        try:
            return method(*fargs, **kwargs)
        except Exception:
            _notify_exception(step_id, sys.exc_info())
            raise
        finally:
            _notify_end(step_id)

    return wrapper


def _notify_start(**options):
    step_id = uuid.uuid4()
    [l.start_step(step_id, **options) for l in listeners]
    return step_id


def _notify_end(step_id, **options):
    [l.end_step(step_id, **options) for l in listeners]


def _notify_exception(step_id, err, **options):
    [l.exception(step_id, err, **options) for l in listeners]

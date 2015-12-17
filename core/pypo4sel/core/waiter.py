import time

from selenium.common.exceptions import TimeoutException

import common


class Waiter(object):
    """
    call ``method(**kwargs)`` at least once, if ``condition(value)`` returns not true
    wait until ``condition(value)`` returns true or ``timeout``.

    Return result of last ``method`` call or rise ``TimeoutException(fail_on_timeout)``
    if fail_on_timeout is not None and time expired

    Example:
        print Waiter(lambda x: x<0).start(lambda: 4, 0)  # immediately print 4

        Waiter(lambda x: x<0)(lambda: 4, 2, "fail")  # after 2 second waiting raise TimeoutException

    """

    def __init__(self, condition):
        self.__condition = condition

    def start(self, method, timeout, fail_on_timeout=None, **kwargs):
        end_time = time.time() + timeout
        value = method(**kwargs)
        check = self.__condition(value)
        while time.time() < end_time and not check:
            time.sleep(common.WAIT_ELEMENT_POLL_FREQUENCY)
            value = method(**kwargs)
            check = self.__condition(value)
        else:
            if not check and fail_on_timeout is not None:
                raise TimeoutException(fail_on_timeout)
        return value

    def __call__(self, method, timeout, fail_on_timeout=None, **kwargs):
        return self.start(method, timeout, fail_on_timeout, **kwargs)


def wait(method, timeout, fail_on_timeout=None, **kwargs):
    """
    Wait ``timeout`` seconds until ``method(**kwargs)`` returns a ``value`` that *bool(value)==True*.
    Returns last ``value``.
     If time expired and ``fail_on_timeout`` specified, then raise TimeoutException.

    :param method:
    :param timeout:
    :param fail_on_timeout:
    :param kwargs:
    :return:
    """
    return Waiter(lambda value: bool(value)).start(method, timeout, fail_on_timeout, **kwargs)


def wait_not(method, timeout, fail_on_timeout=None, **kwargs):
    """
    Wait ``timeout`` seconds until ``method(**kwargs)`` returns a ``value`` that *not value==True*.
    Returns last ``value``.
     If time expired and ``fail_on_timeout`` specified, then raise TimeoutException.

    :param method:
    :param timeout:
    :param fail_on_timeout:
    :param kwargs:
    :return:
    """
    return Waiter(lambda value: not value).start(method, timeout, fail_on_timeout, **kwargs)


def wait_displayed(element, timeout=None, fail_on_timeout=None):
    """
    Wait until element becomes visible or time out.
    Returns true is element became visible, otherwise false.
    If timeout is not specified or 0, then uses specific element wait timeout.
    :param element:
    :param timeout:
    :param fail_on_timeout:
    :return:
    """
    return wait(lambda: element.is_displayed(), timeout or element.wait_timeout, fail_on_timeout)


def wait_not_displayed(element, timeout=None, fail_on_timeout=None):
    """
    Wait until element becomes invisible or time out.
    Returns true is element became invisible, otherwise false.
    If timeout is not specified or 0, then uses specific element wait timeout.
    :param element:
    :param timeout:
    :param fail_on_timeout:
    :return:
    """
    return wait(lambda: not element.is_displayed(), timeout or element.wait_timeout, fail_on_timeout)


# noinspection PyPep8Naming
class skip_implicit_wait(object):
    def __init__(self, element, *elements):
        els = [element]
        els.extend(elements)
        self._timeouts = [(e, e.wait_timeout) for e in els]

    def __enter__(self):
        for e, _ in self._timeouts:
            e.wait_timeout = 0

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, exc_tb):
        for e, t in self._timeouts:
            e.wait_timeout = t

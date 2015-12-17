import functools
import hashlib
import re
import time
import uuid

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, \
    ElementNotVisibleException
from selenium.webdriver.remote.webelement import WebElement

import common
import log2l
from .waiter import wait_displayed, wait


def need_interaction(func):
    @functools.wraps(func)
    def wrap(*args, **kwargs):
        el = args[0]
        el._wait_ready_for_interaction = True
        try:
            return func(*args, **kwargs)
        finally:
            el._wait_ready_for_interaction = False

    return wrap


class PageElement(common.BasePageElement, common.PageElementsContainer, common.FindOverride, WebElement):
    """ Base element for 'page object' pattern.
    Encapsulate logic of changing of context of element usage.

    Catch StaleElementReferenceException, if it occurs, and try to find the element again,
    if element found then continue execution, otherwise raise NoSuchElementException

    Class instance may be used as a part of page object/page block
    or class type may be specified directly as last parameter of find/child_element(s) to wrap found element(s).

    For page object field may be specified __set__ method for more useful interaction with the element.
    In this case ``_fill_owner`` should be called first in the __set__ method.

    Examples:

    class SomePageBlock(PageElement):
        field = PageElement("#field_id")
        element = PageElement("#element_id")

        def do_some_work(self, keys):
            self.field.send_keys(keys)
            self.element.click()
            ....

        def __set__(self, owner, value):
            self._fill_owner(owner)
            self.do_some_work(value)


    class SomePageObject(object):
        element = SomePageBlock("#block_id")

        def __init__(self, driver):
            self.driver = driver

    SomePageObject(driver).element.do_some_work("bla-bla")
    # it equals to
    SomePageObject(driver).element = "bla-bla"

    driver.child_element("another block selector", SomePageBlock).do_some_work("cha-cha-cha")
    # but the following wont work
    driver.child_element("another block selector", SomePageBlock) = "cha-cha-cha"

    """

    def __init__(self, selector, timeout=None, name=None):
        super(PageElement, self).__init__(selector, name, timeout)
        self._parent = None
        self._id = None
        self.__cache = {}
        self._wait_ready_for_interaction = False

    def has_class(self, class_name):
        cls_attr = self.get_attribute('class')
        return False if cls_attr is None else re.search(r'(^|\s){}(\s|$)'.format(class_name), cls_attr) is not None

    def exists(self):
        """
        :return: True if element is present in the DOM, otherwise False.
                Ignore implicit and element timeouts and execute immediately.
        """
        t = self.wait_timeout
        self.wait_timeout = 0
        try:
            self.reload()
            return True
        except NoSuchElementException:
            return False
        finally:
            self.wait_timeout = t

    def is_displayed(self):
        """
        :return: False if element is not present in the DOM or invisible, otherwise True.
                Ignore implicit and element timeouts and execute immediately.

        To wait when element displayed or not, use ``waiter.wait_displayed`` or ``waiter.wait_not_displayed``
        """
        t = self.wait_timeout
        self.wait_timeout = 0
        try:
            return super(PageElement, self).is_displayed()
        except NoSuchElementException:
            return False
        finally:
            self.wait_timeout = t

    @property
    def id(self):
        if self._id is None:
            self.reload()
        return self._id

    @log2l.step
    def send_keys(self, *value):
        super(PageElement, self).send_keys(*value)

    @log2l.step
    def submit(self):
        super(PageElement, self).submit()

    @log2l.step
    @need_interaction
    def click(self):
        super(PageElement, self).click()

    @log2l.step
    @need_interaction
    def clear(self):
        super(PageElement, self).clear()

    def reload(self):
        we = wait(common.find, self.wait_timeout, owner=self._owner, locator=self._locator)
        if not we:
            raise NoSuchElementException("Element with selector {} was not found".format(self._locator))
        self._id = we.id
        self._parent = we.parent
        self.__cache[self._owner] = self._id

    def _fill_owner(self, owner):
        super(PageElement, self)._fill_owner(owner)
        if self.__cached__ and self._id is not None:
            self._id = self.__cache.get(self._owner)

    def _execute(self, command, params=None):
        if not self.__cached__ or self._id is None:
            self.reload()

        execute_attempts = 0
        while True:
            try:
                if self._wait_ready_for_interaction:
                    self._wait_ready_for_interaction = False
                    if not wait_displayed(self):
                        raise ElementNotVisibleException("Element with selector {}".format(self._locator))
                    self._wait_ready_for_interaction = True
                val = super(PageElement, self)._execute(command, params)
                return val
            except StaleElementReferenceException:
                if execute_attempts > common.WAIT_STALE_ELEMENT_MAX_TRY:
                    raise
                time.sleep(common.WAIT_ELEMENT_POLL_FREQUENCY)
                self.reload()
            execute_attempts += 1
        return None

    def __hash__(self):
        return int(hashlib.md5(self.id).hexdigest(), 16)


class _ListItem(object):
    def __init__(self, container, index):
        """
        :type container: PageElementsList
        :param container:
        :param index:
        """
        # noinspection PyArgumentList
        super(_ListItem, self).__init__("no_selector")
        self._container = container
        self._index = index
        self.__cached__ = True
        self._name = "{0}[{1}]".format(container.name, index)

    def reload(self):
        self._container.reload()
        if self._index >= len(self._container):
            raise NoSuchElementException("Element #%i no longer exists in "
                                         "the '%s'" % (self._index, self._container.name))

    @property
    def wait_timeout(self):
        return self._container.wait_timeout

    @wait_timeout.setter
    def wait_timeout(self, t):
        self._container.wait_timeout = t


class PageElementsList(common.BasePageElement):
    """
    Provide list interface for list of page elements.
    The list encapsulate logic of changing of context of elements usage and hold context of element usage.

     Example:

     class Page(SomeBasePageClass):
        table_rows = PageElementsList('tr')

     assert len(Page().table_rows) == 10  # we expect 10 rows
     assert Page().table_rows.is_displayed()  # at least one row is displayed
     assert Page().table_rows[1].is_displayed()  # second row is displayed
     Page().table_rows[0].find_elements('td')[2].click()  # click on third cell of first row

    """

    def __init__(self, selector, el_class=PageElement, timeout=None, name=None):
        """
        :type selector: tuple[str, str]|str
        :param selector:
        :type el_class: T <= PageElement
        :param el_class:
        :type name: str
        :param name:
        :return:
        """
        super(PageElementsList, self).__init__(selector, name, timeout)
        self._el_class = type("ListOf" + el_class.__name__ + uuid.uuid4().get_hex(), (_ListItem, el_class,), {})
        self.__cache = {}
        self.__items = []

    def is_displayed(self):
        """
        :return: True id at least one element is displayed, otherwise False.
                Ignore implicit and element timeouts and execute immediately.
        """
        t = self.wait_timeout
        self.wait_timeout = 0
        try:
            self.reload()
            return any(e.is_displayed() for e in self)
        finally:
            self.wait_timeout = t

    def reload(self):
        # noinspection PyUnresolvedReferences
        # noinspection PySuperArguments
        l = wait(lambda: super(common.FindOverride, self._owner).find_elements(*self._locator), self.wait_timeout)
        cache = [w.id for w in l]
        self.__initialize_elements(cache)
        self.__cache[self._owner] = cache

    def __initialize_elements(self, items):
        new_len = len(items)
        old_len = len(self.__items)
        if new_len > old_len:
            self.__items.extend([self._el_class(self, i) for i in range(old_len, new_len)])
        else:
            del self.__items[new_len:]
        for e, l in zip(self.__items, items):
            setattr(e, "_id", l), setattr(e, "_parent", self._parent)
            setattr(e, "_w3c", self._w3c), setattr(e, "_owner", self._owner)

    def _fill_owner(self, owner):
        super(PageElementsList, self)._fill_owner(owner)
        if self.__cached__ and self._owner in self.__cache:
            self.__initialize_elements(self.__cache[self._owner])

    def __len__(self):
        self.reload()
        return len(self.__items)

    def __getitem__(self, index):
        if not self.__cached__ or self._owner not in self.__cache:
            self.reload()
        try:
            return self.__items[index]
        except IndexError:
            self.reload()
            return self.__items[index]

    def __iter__(self):
        self.reload()
        i = 0
        while True:
            try:
                yield self[i]
                i += 1
            except IndexError:
                return


class VirtualElement(common.BasePageElement, common.PageElementsContainer, common.FindOverride):
    # TODO add parameters to support parametrized selectors for child elements
    def __init__(self, name=None):
        super(VirtualElement, self).__init__(("virtual", "element"), name)

    def _init_element(self, element):
        # noinspection PyProtectedMember
        element._fill_owner(self._owner)
        return element

    def reload(self):
        raise TypeError("VirtualElementsGroup is not supposed to be reloaded, "
                        "it doesn't have corresponding DOM element ")

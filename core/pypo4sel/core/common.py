import inspect
import re
from abc import abstractmethod

import six
from selenium.common.exceptions import InvalidSelectorException, NoSuchElementException
from selenium.webdriver.common.by import By

WAIT_STALE_ELEMENT_MAX_TRY = 5
WAIT_ELEMENT_TIMEOUT = 0
WAIT_ELEMENT_POLL_FREQUENCY = 0.5


def get_members_safety(cls):
    # inspect.getmembers calls __get__ method of the field, if exists, that may cause unexpected actions
    # the solution below does't have this problem
    return reduce(lambda a, b: dict(a, **vars(b)), reversed(inspect.getmro(cls)), {}).items()


class PageElementsContainer(object):
    """
    Classes inheriting PageElementsContainer can use BasePageElement(s) as class attributes
    with implicit element initialization and searching.
    If a class inherits PageElementsContainer and doesn't inherit PageElement,
    than it should have attribute 'driver' with web driver instance.
    """

    def __new__(cls, *args, **kwargs):
        for k, v in get_members_safety(cls):
            if isinstance(v, (BasePageElement,)) and v._name is None:
                v._name = k
        # noinspection PyArgumentList
        return super(PageElementsContainer, cls).__new__(cls, *args, **kwargs)

    def all_elements(self):
        """returns all public BasePageElements grouped by this element and it parent(s)
        :rtype: list[(str, BasePageElement)]
        """
        return [(k, getattr(self, k)) for k, v in get_members_safety(self.__class__)
                if not k.startswith("_") and isinstance(v, (BasePageElement,))]


class BasePageElement(object):
    """
    Base class to describe page object element.
    """

    def __init__(self, selector, name=None, timeout=None, cached=True):
        self.__cached__ = cached
        self._locator = build_locator(selector)
        self._name = name
        self._owner = None
        self._parent = None
        """ :type: FindOverride """
        self.__timeout = timeout
        self._w3c = False

    def _fill_owner(self, owner):
        # _parent and _id field are native for Selenium WebDriver WebElement
        # and should be used in this way for clear and through work with PageElement as WebElement
        if hasattr(owner, "parent"):
            self._parent = owner.parent
            self._owner = owner
        else:
            if not hasattr(owner, "driver"):
                raise TypeError("class {0} doesn't have 'driver' attribute.\n"
                                "Class uses page element(s) should inherit "
                                "PageElement or has 'driver' attribute.".format(type(owner).__name__))
            self._parent = owner.driver
            self._owner = owner.driver
        self._w3c = getattr(self._parent, "w3c", False)

    # noinspection PyUnusedLocal
    def __get__(self, owner, cls):
        self._fill_owner(owner)
        return self

    @abstractmethod
    def reload(self):
        pass

    @property
    def wait_timeout(self):
        return WAIT_ELEMENT_TIMEOUT if self.__timeout is None else self.__timeout

    @wait_timeout.setter
    def wait_timeout(self, value):
        self.__timeout = value if isinstance(value, (float, int)) and value >= 0 else None

    @property
    def name(self):
        return self._name or "({}:{})".format(*self._locator)


def define_selector(by, value, el_class):
    """
    :param by:
    :param value:
    :param el_class:
    :rtype: tuple[type, str|tuple[str, str]]
    :return:
    """
    el = el_class
    selector = by
    if isinstance(value, six.string_types):
        selector = (by, value)
    elif value is not None:
        el = value

    if el is None:
        el = elements.PageElement

    return el, selector


class FindOverride(object):
    def child_element(self, by=By.ID, value=None, el_class=None):
        """
        Doesn't rise NoSuchElementException in case if there are no element with the selector.
        In this case ``exists()`` and ``is_displayed()`` methods of the element will return *False*.
        Attempt to call any other method supposed to interact with browser will raise NoSuchElementException.

        usages with ``'one string'`` selector:
         - find_element(by: str) -> PageElement
         - find_element(by: str, value: T <= PageElement) -> T

        usages with ``'webdriver'`` By selector
         - find_element(by: str, value: str) -> PageElement
         - find_element(by: str, value: str, el_class: T <= PageElement) -> T

        :type by: str
        :param by:
        :type value: str | T <= PageElement
        :param value:
        :type el_class: T <= PageElement
        :param el_class:
        :rtype: T <= PageElement
        :return:
        """
        el, selector = define_selector(by, value, el_class)
        return self._init_element(el(selector))

    def child_elements(self, by=By.ID, value=None, el_class=None):
        """
        alias for ``find_elements``
        :param by:
        :param value:
        :param el_class:
        :return:
        """
        el, selector = define_selector(by, value, el_class)
        return self._init_element(elements.PageElementsList(selector, el))

    def find_element(self, by=By.ID, value=None, el_class=None):
        """
        usages with ``'one string'`` selector:
         - find_element(by: str) -> PageElement
         - find_element(by: str, value: T <= PageElement) -> T

        usages with ``'webdriver'`` By selector
         - find_element(by: str, value: str) -> PageElement
         - find_element(by: str, value: str, el_class: T <= PageElement) -> T

        :type by: str
        :param by:
        :type value: str | T <= PageElement
        :param value:
        :type el_class: T <= PageElement
        :param el_class:
        :rtype: T <= PageElement
        :return:
        """
        el = self.child_element(by, value, el_class)
        el.reload()
        return el

    def find_elements(self, by=By.ID, value=None, el_class=None):
        """
        usages with ``'one string'`` selector:
         - find_elements(by: str) -> PageElementsList[ListElement]
         - find_elements(by: str, value: T <= ListElement) -> PageElementsList[T]

        usages with ``'webdriver'`` By selector
         - find_elements(by: str, value: str) -> PageElementsList[ListElement]
         - find_elements(by: str, value: str, el_class: T <= ListElement) -> PageElementsList[T]

        :type by: str
        :param by:
        :type value: str | T <= ListElement
        :param value:
        :type el_class: T <= ListElement
        :param el_class:
        :rtype: PageElementsList[T | ListElement]
        :return:
        """
        els = self.child_elements(by, value, el_class)
        els.reload()
        return els

    def _init_element(self, element):
        # noinspection PyProtectedMember
        element._fill_owner(self)
        return element


import elements


def _stats_with(prefix):
    return lambda s: s.startswith(prefix)


selectors = [
    (re.compile(r"^\w+$").match, By.TAG_NAME, None),
    (re.compile(r"^\.-?[_a-zA-Z]+[_a-zA-Z0-9-]*$").match, By.CLASS_NAME, 1),
    (re.compile(r"^#[A-Za-z]+[:._a-zA-Z0-9-]*$").match, By.ID, 1),
    (re.compile(r"^@[A-Za-z]+[:._a-zA-Z0-9-]*$").match, By.NAME, 1),
    (re.compile(r"^(\./|//).+").match, By.XPATH, None),
    (_stats_with("$x:"), By.XPATH, 3),
    (_stats_with("$link_text:"), By.LINK_TEXT, 11),
    (_stats_with("$partial_link_text:"), By.PARTIAL_LINK_TEXT, 19),
    (re.compile(r"^(\*|\.|#|[\w-]|\[|:).*").match, By.CSS_SELECTOR, None)
]


def build_locator(selector):
    """
    - ID = "#valid_id"
    - CLASS_NAME = ".valid_class_name"
    - TAG_NAME = "valid_tag_name"
    - XPATH = start with "./" or "//" or "$x:"
    - LINK_TEXT = start with "$link_text:"
    - PARTIAL_LINK_TEXT = start with "$partial_link_text:"
    - NAME = "@valid_name_attribute_value"

    CSS_SELECTOR = all other that starts with *|.|#|[\w-]|\[|:

    :type selector: str|tuple
    :param selector:
    :rtype: tuple[selenium.webdriver.common.by.By, str]
    :return:
    """
    if type(selector) is tuple:
        return selector
    if not isinstance(selector, six.string_types):
        raise InvalidSelectorException("Invalid locator values passed in")

    s = selector.strip()
    for test, by, index in selectors:
        if test(s):
            return by, s[index:]
    raise InvalidSelectorException("Invalid locator values passed in: {}".format(selector))


def find(owner, locator):
    try:
        return super(FindOverride, owner).find_element(*locator)
    except NoSuchElementException:
        return False

from collections import Sequence

import pytest
from selenium.common.exceptions import NoSuchElementException

from pypo4sel.core.common import BasePageElement
from pypo4sel.core.webdrivers import FirefoxDriver

"""
cases:
    #   | exits | find | child | finds | childs | exists | display | text
    0   | +     | el   | el    | [el]  | [el]   | +      | +       | +
    1   | -     | ex   | el    | []    | []     | -      | -       | ex


"""


@pytest.fixture(scope="module")
def driver(request):
    drv = FirefoxDriver()
    request.addfinalizer(lambda: drv.close())
    return drv


def test_find_rise_exception_when_no_element(driver):
    """
    :type driver: FirefoxDriver
    :return:
    """
    with pytest.raises(NoSuchElementException) as ex:
        driver.find_element("id")
    assert ex.type == NoSuchElementException


def test_child_return_element_when_no_element(driver):
    """
    :type driver: FirefoxDriver
    :return:
    """
    e = driver.child_element("id")
    assert e is not None
    assert not e.exists()
    assert not e.is_displayed()
    with pytest.raises(NoSuchElementException) as ex:
        e.click()
    assert ex.type == NoSuchElementException


def test_find_elements_when_no_element(driver):
    e = driver.find_elements("id")
    assert e is not None
    assert isinstance(e, Sequence)
    assert isinstance(e, BasePageElement)
    assert not e.is_displayed()
    assert 0 == len(e)


def test_child_elements_equal_find_elements_when_no_element(driver):
    e = driver.child_elements("id")
    assert e is not None
    assert isinstance(e, Sequence)
    assert isinstance(e, BasePageElement)
    assert not e.is_displayed()
    assert 0 == len(e)


def test_exists_return_true_if_element_found_wi_elementth_find():
    pass

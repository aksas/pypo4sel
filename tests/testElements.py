import unittest

from mock import patch, Mock
from selenium.common.exceptions import InvalidSelectorException, NoSuchElementException
from selenium.webdriver.common.by import By

from pypo4sel.core.common import BasePageElement, PageElementsContainer, FindOverride
from pypo4sel.core.common import build_locator
from pypo4sel.core.elements import PageElement, PageElementsList
from pypo4sel.core.elements import WebElement


class TestBuildLocator(unittest.TestCase):
    def test_tuple_in(self):
        i = ("a", "b")
        r = build_locator(i)
        self.assertEqual(r, i)

    def test_exception_for_invalid_type(self):
        with self.assertRaises(InvalidSelectorException):
            # noinspection PyTypeChecker
            build_locator(1)

    def test_id(self):
        self.assertEqual((By.ID, "id"), build_locator("#id"))
        self.assertEqual((By.ID, "i_12d"), build_locator(" #i_12d "))

    def test_class(self):
        self.assertEqual((By.CLASS_NAME, "id"), build_locator(".id"))
        self.assertEqual((By.CLASS_NAME, "i_12d"), build_locator(" .i_12d "))

    def test_tag_name(self):
        self.assertEqual((By.TAG_NAME, "id"), build_locator("id"))
        self.assertEqual((By.TAG_NAME, "i_12d"), build_locator(" i_12d "))

    def test_exception_when_invalid_short(self):
        with self.assertRaises(InvalidSelectorException):
            build_locator("$adsa")
        with self.assertRaises(InvalidSelectorException):
            build_locator(",adsa")

    def test_xpath(self):
        self.assertEqual((By.XPATH, "./id[sdf]"), build_locator("./id[sdf]"))
        self.assertEqual((By.XPATH, "i_12d"), build_locator(" $x:i_12d "))
        self.assertEqual((By.XPATH, "//i_12d"), build_locator(" //i_12d "))

    def test_css(self):
        self.assertEqual((By.CSS_SELECTOR, "id[sdf]"), build_locator("id[sdf]"))
        self.assertEqual((By.CSS_SELECTOR, ".xpath:i_12d"), build_locator(" .xpath:i_12d "))
        self.assertEqual((By.CSS_SELECTOR, "#i_12d>23 re"), build_locator("#i_12d>23 re"))
        self.assertEqual((By.CSS_SELECTOR, ".sss.ddd"), build_locator(".sss.ddd"))
        self.assertEqual((By.CSS_SELECTOR, "sss .ddd"), build_locator("sss .ddd"))
        self.assertEqual((By.CSS_SELECTOR, "#sss ddd"), build_locator("#sss ddd"))


class TestFindOverride(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestFindOverride, cls).setUpClass()
        cls.longMessage = True
        cls.sut = FindOverride()

    @patch('pypo4sel.core.elements.PageElement')
    def test_default_element_class_in_find(self, mock_element):
        self.assertEqual(self.sut.find_element("", ""), mock_element.return_value)

    def test_find_returns_element_with_passed_type(self):
        cls = Mock()
        inst = cls.return_value
        # noinspection PyTypeChecker
        self.assertEqual(inst, self.sut.find_element("", "", cls))

    @patch('pypo4sel.core.elements.PageElement')
    def test_find_passes_given_parameters_to_created_element(self, mock_element):
        self.sut.find_element("by", "value")
        mock_element.assert_called_once_with(("by", "value"))

    @patch('pypo4sel.core.elements.PageElement')
    def test_fill_owner_is_called(self, mock_element):
        self.sut.find_element("", "")
        # noinspection PyUnresolvedReferences
        mock_element.return_value._fill_owner.assert_called_once_with(self.sut)

    @patch('pypo4sel.core.elements.PageElement')
    def test_reload_is_called(self, mock_element):
        self.sut.find_element("", "")
        mock_element.return_value.reload.assert_called_once_with()

    # noinspection PyUnresolvedReferences
    @patch('pypo4sel.core.elements.PageElementsList')
    def test_find_elements(self, mock_element):
        l = self.sut.find_elements()
        l._fill_owner.assert_called_once_with(self.sut)

        self.assertEqual(l, mock_element.return_value, "returned type is wrong")


# noinspection PyUnresolvedReferences
class TestBasePageElement(unittest.TestCase):
    def test_default_constructor(self):
        sut = BasePageElement("by selector")
        self.assertTrue(sut.__cached__)
        self.assertEqual(sut._locator, ("css selector", 'by selector'))
        self.assertIsNone(sut._name)
        self.assertIsNone(sut._owner)

    def test_constructor_with_name(self):
        sut = BasePageElement(("by", 'selector'), "name")
        self.assertEqual(sut._locator, ("by", 'selector'))
        self.assertEqual(sut._name, "name")

    @patch('pypo4sel.core.common.build_locator')
    def test_build_selector_called_in_constructor(self, m):
        BasePageElement("by", 'selector')
        m.assert_called_once_with("by")

    @patch.object(BasePageElement, "_fill_owner")
    def test_get_calls_fill_owner_anr_returns_self(self, mth):
        sut = BasePageElement("by", 'selector')
        r = sut.__get__("owner", "cls")
        mth.assert_called_once_with("owner")
        self.assertEqual(r, sut)

    def test_fill_owner_without_driver(self):
        sut = BasePageElement("by", 'selector')
        with self.assertRaises(TypeError):
            sut._fill_owner(1)
        with self.assertRaises(TypeError):
            sut._fill_owner(None)

    def test_fill_owner_with_driver(self):
        c = type("Container", (object,), {'driver': 'driver'})
        sut = BasePageElement("by", 'selector')
        sut._fill_owner(c)
        self.assertEqual(sut._owner, 'driver')
        self.assertEqual(sut._parent, 'driver')

    def test_fill_owner_with_page_element(self):
        sut = BasePageElement("by")
        el = PageElement("q")
        el._parent = 'parent'
        el._id = '1'
        sut._fill_owner(el)
        self.assertEqual(sut._owner, el)
        self.assertEqual(sut._parent, 'parent')


# noinspection PyUnresolvedReferences
class TestPageElementContainer(unittest.TestCase):
    def setUp(self):
        class ContainerClass(PageElementsContainer):
            driver = 'driver'

        self.container_cls = ContainerClass

    def test_auto_name(self):
        setattr(self.container_cls, "page_element", BasePageElement("s"))
        c = self.container_cls()
        self.assertEqual("page_element", c.page_element._name)

    def test_preserve_default_name(self):
        setattr(self.container_cls, "page_element", BasePageElement("s", "default name"))
        c = self.container_cls()
        self.assertEqual("default name", c.page_element._name)

    def test_auto_name_for_inherit_field(self):
        setattr(self.container_cls, "page_element", BasePageElement("s"))
        cc = type("inherited", (self.container_cls,), {})
        c = cc()
        self.assertEqual("page_element", c.page_element._name)

    def test_auto_name_for_multi_base(self):
        inh = type("inh", (self.container_cls,), {})
        inh1 = type("inh1", (self.container_cls,), {})
        setattr(inh, "page_element", BasePageElement("s"))

        cc = type("inherited", (inh1, inh), {})
        c = cc()
        self.assertEqual("page_element", c.page_element._name)


# noinspection PyUnresolvedReferences
class TestPageElement(unittest.TestCase):
    def setUp(self):
        owner = PageElement("o")
        owner._id = "33"
        sut = PageElement("selector")
        sut._owner = owner
        self.sut = sut

    @patch.object(WebElement, "find_element")
    def test_reload_calls_webelement_find(self, mock):
        self.sut.reload()
        mock.assert_called_once_with("tag name", "selector")

    @patch.object(WebElement, "find_element")
    def test_reload_raise_exception_if_there_are_no_element(self, mock):
        mock.return_value = False
        with self.assertRaises(NoSuchElementException):
            self.sut.reload()

    @patch.object(WebElement, "find_element")
    def test_reload_map_id_and_parent(self, mock):
        mock.return_value = type('mock_we', (object,), dict(id="id", parent="parent"))
        self.sut.reload()
        self.assertEqual("id", self.sut.id)
        self.assertEqual("parent", self.sut.parent)

    @patch.object(WebElement, "find_element")
    def test_reload_waiting(self, mock):
        import time

        mock.return_value = False
        self.sut.wait_timeout = 1
        t = time.time()
        try:
            self.sut.reload()
        except NoSuchElementException:
            pass
        finally:
            self.assertAlmostEqual(time.time() - t, 1, delta=0.01)

    @patch.object(WebElement, "is_displayed")
    def test_is_displayed_calls_native_is_displayed(self, mock):
        self.sut.is_displayed()
        mock.assert_called_once()

    @patch.object(PageElement, "_execute")
    def test_is_displayed_calls_execute(self, mock):
        self.sut.is_displayed()
        mock.assert_called_once()

    @patch.object(PageElement, "_execute")
    def test_is_displayed_return_false_if_there_are_no_element(self, mock):
        mock.side_effect = NoSuchElementException
        self.assertFalse(self.sut.is_displayed())

    @patch.object(WebElement, "find_element")
    def test_is_displayed_return_false_if_there_are_no_element_mock_find(self, mock):
        mock.return_value = False
        self.assertFalse(self.sut.is_displayed())


# noinspection PyUnresolvedReferences
class TestElementList(unittest.TestCase):
    def setUp(self):
        owner = PageElement("o")
        owner._id = '123'
        sut = PageElementsList("selector")
        sut._owner = owner
        sut._parent = "parent"
        self.sut = sut

    @patch.object(WebElement, "find_elements")
    def test_reload_calls_native_find_elements(self, mock):
        mock.return_value = [type('el', (object,), dict(id=i)) for i in range(3)]
        self.sut.reload()
        mock.assert_called_once_with("tag name", "selector")
        self.assertEqual(3, len(self.sut))
        self.assertEqual(self.sut[0].id, 0)
        self.assertEqual(self.sut[0].parent, "parent")
        self.assertEqual(self.sut[0]._index, 0)
        self.assertEqual(self.sut[2].id, 2)
        self.assertEqual(self.sut[2].parent, "parent")
        self.assertEqual(self.sut[2]._index, 2)

    @patch.object(WebElement, "find_elements")
    def test_list_element_reload(self, mock):
        mock.return_value = [type('el', (object,), dict(id=i)) for i in range(3)]
        self.sut.reload()

        mock.return_value = [type('el', (object,), dict(id=5 + i)) for i in range(4)]
        self.sut[0].reload()

        self.assertEqual(4, len(self.sut))
        self.assertEqual(self.sut[0].id, 5)
        self.assertEqual(self.sut[0].parent, "parent")
        self.assertEqual(self.sut[0]._index, 0)

        self.assertEqual(self.sut[3].id, 8)
        self.assertEqual(self.sut[3].parent, "parent")
        self.assertEqual(self.sut[3]._index, 3)

    @patch.object(WebElement, "find_elements")
    def test_exception_on_reload(self, mock):
        mock.return_value = [type('el', (object,), dict(id=i, parent='parent%i' % i)) for i in range(3)]
        self.sut.reload()

        mock.return_value = [type('el', (object,), dict(id=5 + i, parent='parent%i' % i)) for i in range(2)]
        with self.assertRaises(NoSuchElementException):
            self.sut[2].reload()

    @patch.object(WebElement, "find_elements")
    def test_list_element_is_displayed(self, mock):
        mock.return_value = [type('el', (object,), dict(id=i, parent='parent%i' % i)) for i in range(3)]
        self.sut.reload()

        mock.return_value = [type('el', (object,), dict(id=5 + i, parent='parent%i' % i)) for i in range(2)]
        self.sut[2].__cached__ = False
        self.assertFalse(self.sut[2].is_displayed())

    @patch.object(WebElement, "find_elements")
    @patch.object(WebElement, "is_displayed")
    def test_list_is_displayed(self, d, fe):
        fe.return_value = [type('el', (object,), dict(id=i, parent='parent%i' % i)) for i in range(3)]
        d.return_value = True
        self.sut.reload()
        self.assertTrue(self.sut.is_displayed())

        d.return_value = False
        self.assertFalse(self.sut.is_displayed())

        d.return_value = [True, False, False]
        self.assertTrue(self.sut.is_displayed())

        fe.return_value = []
        self.sut.reload()
        self.assertFalse(self.sut.is_displayed())

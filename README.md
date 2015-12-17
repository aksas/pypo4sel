# pypo4sel

## core

Wrapper for selenium webdriver to make page objects easy:

install:
> pip install pypo4sel.core

```python
class SomePageBlock(PageElement):
    filed = PageElement("#filed_id", timeout=10)
    button = PageElement("//path/to/element")

    def do_some_work(self, keys):
        self.field.send_keys(keys)
        self.button.click()
        ...

class SomePageObject(PageElementsContainer):
    element = SomePageBlock(".block_class")

    def __init__(self, driver):
        self.driver = driver

page = SomePageObject(get_driver('firefox'))
assert page.element.button.is_displayed()
page.element.do_some_work("bla-bla")
```

- lazy element loading by request
- automated handling of `StaleElementReferenceException`
- flexible timeouts
- automated detecting of locator type
- smart lists of elements, automated logs and much more [here](core/README.md).

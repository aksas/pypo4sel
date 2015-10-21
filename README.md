# pypo4sel
Simple page object framework for selenium and python

```python

    class SomePageBlock(PageElement):
        filed = PageElement("#filed_id", timeout=10)
        button = PageElement("#button_id")

        def do_some_work(self, keys):
            self.field.send_keys(keys)
            self.button.click()
            ...

    class SomePageObject(PageElementsContainer):
        element = SomePageBlock("#block_id")

        def __init__(self, driver):
            self.driver = driver
    
    page = SomePageObject(driver)
    assert page.element.button.is_displayed()
    page.element.do_some_work("bla-bla")
```    

with automated handling of StaleElementReferenceException

that allows using page blocks without page
```python
    driver.find_element("#block_id", SomePageBlock).do_some_work("cha-cha-cha")
```

and may be used in 'classic' way
```python
    block = driver.find_element(By.ID, "block_id")
    button = block.find_element_by_id("button_id")
    assert button.is_displayed()
```

> with one little difference - `is_displayed()` is executed immediately independent of any timeouts, 
but `waiter.wait_displayed` and `waiter.wait_not_displayed` may be helpful to organize waiting.


and a little bit not 'classic'
```python
    block = driver.child_element(By.ID, "not existing")
    assert not block.exists()  # pass
    assert not block.is_displayed()  # pass
    block.click()  # raise NoSuchElementException
```

for page element the behaviour is the same 
```python
    assert not page.not_existing_element.exists()  # pass
    assert not page.not_existing_element.is_displayed()  # pass
    page.not_existing_element.click()  # raise NoSuchElementException
```


Work with list of elements is simple
```python
    class Page(SomeBasePageClass):
        table_rows = PageElementsList('tr')

    assert len(Page().table_rows) == 10  # we expect 10 rows
    assert Page().table_rows.is_displayed()  # at least one row is displayed
    assert Page().table_rows[1].is_displayed()  # second row is displayed
    Page().table_rows[0].find_elements('td')[2].click()  # click on third cell of first row
```

but powerful
```python
    class ComplexElement(PageElement):
        field = PageElement("selector")
        nested_block = SomePageBlock("block")
        
        def actions(self):
            ...
            
        # anything else
    
    class Page(SomeBasePageClass):
        element_list = PageElementsList('li', ComplexElement)

    for e in Page().element_list:
        e.nested_block.do_some_work(e.field.text)
        e.action()
```



And a few words about 
### waiting
```python
    class MyPage(PageElementsContainer):
        element = PageElement('selector', timeout=11)
        elements_list = PageElementList('//list[@selector]')
        not_existing_element = PageElement('ddddd')
        
        def __init__(self, driver):
            self.driver = driver
    
    driver = get_driver()
    driver.implicitly_wait(5)  # for all elements set default timeout to 5 sec
    page = MyPage(driver)
    
    # immediately check if element is not displayed
    assert not page.element.is_displayed()
    # if element is displayed, wait not more 11 sec until element disappear
    wait_not_displayed(page.element)  
    # if element is displayed, wait not more 30 sec until element disappear
    wait_not_displayed(page.element, timeout=30)  
    # wait 5 sec until at least one element of the list exists and displayed
    wait_displayed(page.elements_list)  
```

to combine implicit and explicit waiting
```python
    old_wait = page.elements_list.wait_timeout
    page.elements_list.wait_timeout = 0
    wait(lambda: len(page.elements_list) > 3, 20)  # skip element waiting
    page.elements_list.wait_timeout = old_wait
```
or
```python
    with skip_implicit_wait(page.elements_list):
        wait(lambda: len(page.elements_list) > 3, 20)
```    

timeout exception
```python    
    assert not page.not_existing_element.is_displayed()  # pass
    # will rise TimeoutException with exception_message after 2 sec waiting
    wait_displayed(page.not_existing_element, fail_on_timeout="exception_message")  
```


so
* no StaleElementReferenceException
* lazy initialization of elements
* minimum requests to webdriver
* short selectors
* flexible management of timeouts: common and individual implicit timeouts, easy combined with explicit

and something else...

### logging
the following *native* actions log himself automatically:
  * send_keys(self, *value)
  * submit(self)
  * click(self)
  * clear(self)
    
to subscribe to logging actions create class inherits pypo4sel.core.log2l.ListenerMixin, implement appropriate evenets and add it to the list of listeners:
```python    
import pypo4sel.core.log2l as log

class MyLogger(log.ListenerMixin):
    def start_step(self, step_id, **options):
        # step_id is uuid4
        # options with which a step is started
        do_some_logging_stuff_here

    def end_step(self, step_id):
        do_some_actions_to_close_log_section_if_needed

    def exception(self, step_id, exc_type, exc_val, exc_tb):
        log_exeption_here #  exception will be reraised automaticaly

    def message(self, msg, **kwargs):
        pass 
        
log.listeners.add(MyLogger())
```

After that, each time when an *action* will be called the 'start_step' will be called with the following 'options':
``` 
 {
    'element_name':'name_of_element_or_selector',
    'step_name':'action name',
 }
```

and for `send_keys`
```
 {
    'element_name': 'name_of_element_or_selector',
    'step_name': 'send_keys',
    'args': value
 }
```

also any custom method may be wrapped as an step
```python

class Element(PageElement):
    @log.step
    def method(self, *fargs, **fkwargs):
        do_smth_here

    @log.step("any text")
    def another_method(self, *fargs, **fkwargs):
        self.click()

        
class Page(object):
    my_element = Element('#id')
```

each time when 'method' will be called the 'start_step' will be called with the following 'options':
```
 {
    'element_name':'my_element',
    'step_name':'method',
    'args':<fargs>,
    'kwargs':<fkwargs>
 }
```
for 'another_method' will be called the 'start_step' with:
```
 {
    'first_param':'any text'
    'element_name':'my_element',
    'step_name':'another_method',
    'args':<fargs>,
    'kwargs':<fkwargs>
 }
```
and *nested* action 'click'
```
 {
    'element_name':'my_element',
    'step_name':'click',
 }
```

and `step` may be used as context
```python
with log.step('group of actions or smth like this'):
    action1()
    ....
```

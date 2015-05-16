# pypo4sel
Simple page object framemework for selenium and python

```python
  class ComplexElement(PageElement):
    button = PageElement('#button_id')
    edit = PageElement('#edit_id')
    
    def fill_and_go(self, text)
      self.edit.type(text)
      self.button.click()
    
    @property
    def text(self):
      return self.edit.text


  class MyPage(WebPage):
    caption = PageElement('title')
    search = ComplexElement('div.search')
```

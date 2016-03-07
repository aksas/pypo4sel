from distutils.core import setup

long_description = """
pypo4sel.core
--------------------------------------------------------

Wrapper for selenium webdriver to make page objects easy::

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


- lazy element loading by request
- automated handling of `StaleElementReferenceException`
- flexible timeouts
- automated detecting of locator type
- smart lists of elements, automated logs and much more `here <http://github.com/aksas/pypo4sel>`_.
"""

setup(
    name='pypo4sel.core',
    version='0.0.2',
    packages=['pypo4sel', 'pypo4sel.core'],
    url='https://github.com/aksas/pypo4sel',
    license='MIT',
    author='Oleksii Skliarov',
    author_email='oleksii.skliarov@gmail.com',
    description='page object wrapper for selenium webdriver',
    long_description=long_description,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    keywords=['selenium', 'webdriver', 'automated', 'testing', 'page object'],
    install_requires=['six', 'selenium'],
)

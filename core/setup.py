from distutils.core import setup

long_description = ""

setup(
    name='pypo4sel.core',
    version='0.0.2',
    packages=['pypo4sel', 'pypo4sel.core'],
    url='https://github.com/aksas/pypo4sel/tree/master/core',
    license='MIT',
    author='aksas',
    author_email='',
    description='page object wrapper for selenium webdriver',
    long_description=long_description,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='selenium webdriver automated testing',
    install_requires=['six', 'selenium'],
)

from distutils.core import setup

setup(
    name='pypo4sel.core',
    version='0.0.4',
    packages=['pypo4sel', 'pypo4sel.core', 'pypo4sel.examples'],
    url='https://github.com/aksas/pypo4sel/tree/few_packages/core',
    license='MIT',
    author='Oleksii Skliarov',
    author_email='oleksii.skliarov@gmail.com',
    description='page object wrapper for selenium webdriver',
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

from setuptools import setup

setup(
    name='NoseLog2l',
    install_requires=['nose'],
    py_modules=['pypo4nose'],
    entry_points={
      'nose.plugins.0.10': [
        'pyponose = simple_nose:PypoNose'
      ]
    }
)
from setuptools import setup

setup(
    name='NoseLog2l',
    install_requires=['nose==1.3.0'],
    py_modules=['simple_nose'],
    entry_points={
      'nose.plugins.0.10': [
        'pyponose = simple_nose:PypoNose'
      ]
    }
)
import unittest

from pypo4sel.core import log2l

log2l.message("init module")


@log2l.step
def common_actions():
    log2l.message('do some stuff')


class TestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestTest, cls).setUpClass()
        log2l.message('setup class')

    def setUp(self):
        super(TestTest, self).setUp()
        log2l.message('set up')

    @classmethod
    def tearDownClass(cls):
        super(TestTest, cls).tearDownClass()
        log2l.message('teardown class')

    def tearDown(self):
        super(TestTest, self).tearDown()
        log2l.message('tear down')

    def test(self):
        common_actions()
        log2l.message('test')
        assert True

    def test_fail(self):
        with log2l.action('silent'):
            common_actions()
        log2l.message('test fail')
        assert False


import nose
from examples.simple_logger import PypoNose

if __name__ == '__main__':
    pl = PypoNose()
    result = nose.run(addplugins=[pl], argv=['', '--with-pyponose'])

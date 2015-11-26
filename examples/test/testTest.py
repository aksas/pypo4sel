import unittest
import nose

from pypo4sel.core import log2l

# log2l.message("init module")
#
#
# def test_single():
#     with log2l.step("check point"):
#         assert True
#
#
# @log2l.step
# def common_actions():
#     log2l.message('do some stuff')
#
#
# class TestFewTest(unittest.TestCase):
#     """
#     ### class level description
#     nested test description expected below:
#     ---
#     """
#     @classmethod
#     def setUpClass(cls):
#         super(TestFewTest, cls).setUpClass()
#         log2l.message('setup class')
#
#     def setUp(self):
#         super(TestFewTest, self).setUp()
#         log2l.message('set up')
#
#     @classmethod
#     def tearDownClass(cls):
#         super(TestFewTest, cls).tearDownClass()
#         log2l.message('teardown class')
#
#     def tearDown(self):
#         super(TestFewTest, self).tearDown()
#         log2l.message('tear down')
#
#     def test(self):
#         """
#         common test checked:
#         * one
#         * two
#         """
#         common_actions()
#         log2l.message('test')
#         assert True
#
#     def test_fail(self):
#         with log2l.action('silent'):
#             common_actions()
#         log2l.message('test fail')
#         assert False, 'fail message'
#
#     def test_raise(self):
#         raise Exception('oooo')
#
#     @unittest.skip
#     def test_skip(self):
#         pass


@log2l.action
def act():
    with log2l.step('do stuff'):
        log2l.message('yep')
        raise Exception('aaaaa')


class TestOneTest(unittest.TestCase):
    """
    ### class level description

    nested test description expected below:

    - - -
    """

    def tearDown(self):
        log2l.message('Test Done')

    def test_fail(self):
        """ common test checked:

        * one
        * two
        """
        with log2l.step('ready'):
            act()
            log2l.message('done')
        assert True
        # with log2l.step("failed action"):
        #     assert False, 'fail message'


from examples.simple_nose import PypoNose

if __name__ == '__main__':
    # pl = PypoNose() addplugins=[pl],
    pl = PypoNose()
    result = nose.run(plugins=[pl], argv=['', '--with-pyponose'])

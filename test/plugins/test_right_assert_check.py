"""Test right_assert_check.py"""

import astroid
from pylint.testutils import CheckerTestCase, Message
import pytest

from edx_lint.pylint.right_assert_check import AssertChecker
from ..utils import get_module


class TestAssertChecker(CheckerTestCase):
    """Test right_assert_check.py"""

    CHECKER_CLASS = AssertChecker

    def test_good_asserts(self):
        node = astroid.extract_node("""
        import unittest

        class TestStringMethods(unittest.TestCase):
            def test_right_usage(self):
                # This is the right usage of various assert functions.
                self.assertEqual('foo'.upper(), 'FOO')

                true = True
                self.assertTrue(true)
                self.assertFalse(not true)

                self.assertIn("a", "lala")
                self.assertNotIn("b", "lala")

                self.assertGreater(1, 0)
                self.assertLess(1, 2)

            def test_chained_comparisons(self):
                # These uses of assertTrue and assertFalse are fine, because we can't
                # pick apart the chained comparisons.
                my_value = my_other_value = 10
                self.assertTrue(0 < my_value < 1000)
                self.assertFalse(0 < my_value < 5)
                self.assertTrue(my_value == my_other_value == 10)

            def test_other_functions(self):
                foo(bar)
                assertTrue("what is this?")
        """)
        module = get_module(node)

        with self.assertNoMessages():
            self.walk(module)

    @pytest.mark.parametrize("code, better", [
        ("assertTrue('foo'.upper() == 'FOO')", "assertEqual"),
        ("assertFalse(500 == 501)", "assertNotEqual"),
        ("assertTrue('a' in 'lala')", "assertIn"),
        ("assertFalse('b' not in 'lala')", "assertIn"),
        ("assertTrue(1 > 0)", "assertGreater"),
        ("assertFalse(1 < 2)", "assertGreaterEqual"),
        ("assertTrue(my_zero is 0)", "assertIs"),
        ("assertFalse(my_zero is 1)", "assertIsNot"),
        ("assertTrue(my_zero is not 1)", "assertIsNot"),
        ("assertFalse(my_zero is not 0)", "assertIs"),
        ("assertTrue(my_none is None)", "assertIsNone"),
        ("assertFalse(my_zero is None)", "assertIsNotNone"),
        ("assertTrue(my_zero != None)", "assertIsNotNone"),
    ])
    def test_wrong_usage(self, code, better):
        node = astroid.extract_node("""
        import unittest

        class TestStringMethods(unittest.TestCase):
            def test_wrong_usage(self):
                self.{}      #@
        """.format(code))
        module = get_module(node)

        expected = Message(
            msg_id='wrong-assert-type',
            node=node,
            args='{} should be {}'.format(code, better),
        )
        with self.assertAddsMessages(expected):
            self.walk(module)

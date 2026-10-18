import sys
import os
import math
import unittest

# Get the path to the project's root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from src import calculator


class TestValidation(unittest.TestCase):

    def setUp(self):
        # Inputs that every function must reject: strings, None, booleans, NaN and infinity
        self.invalid_inputs = ["2", None, True, False, math.nan, math.inf, -math.inf, [1]]
        self.two_arg_funcs = [
            calculator.add,
            calculator.subtract,
            calculator.multiply,
            calculator.divide,
            calculator.power,
            calculator.modulo,
        ]
        self.three_arg_funcs = [calculator.add_three, calculator.average]

    def test_is_num_accepts_finite_numbers(self):
        for value in [0, -1, 2.5, -0.0, 10**20]:
            with self.subTest(value=value):
                self.assertTrue(calculator.is_num(value))

    def test_is_num_rejects_invalid(self):
        for value in self.invalid_inputs:
            with self.subTest(value=value):
                self.assertFalse(calculator.is_num(value))

    def test_two_arg_funcs_reject_invalid(self):
        for func in self.two_arg_funcs:
            for bad in self.invalid_inputs:
                for args in [(bad, 1), (1, bad)]:
                    with self.subTest(func=func.__name__, args=args):
                        with self.assertRaises(ValueError):
                            func(*args)

    def test_three_arg_funcs_reject_invalid(self):
        for func in self.three_arg_funcs:
            for bad in self.invalid_inputs:
                for args in [(bad, 1, 1), (1, bad, 1), (1, 1, bad)]:
                    with self.subTest(func=func.__name__, args=args):
                        with self.assertRaises(ValueError):
                            func(*args)


class TestBasicArithmetic(unittest.TestCase):

    def test_add(self):
        for x, y, expected in [(2, 3, 5), (5, 0, 5), (-1, 1, 0), (-1, -1, -2)]:
            with self.subTest(x=x, y=y):
                self.assertEqual(calculator.add(x, y), expected)

    def test_add_floats(self):
        self.assertAlmostEqual(calculator.add(0.1, 0.2), 0.3)

    def test_subtract(self):
        for x, y, expected in [(2, 3, -1), (5, 0, 5), (-1, 1, -2), (-1, -1, 0)]:
            with self.subTest(x=x, y=y):
                self.assertEqual(calculator.subtract(x, y), expected)

    def test_multiply(self):
        for x, y, expected in [(2, 3, 6), (5, 0, 0), (-1, 1, -1), (-1, -1, 1), (2.5, 4, 10.0)]:
            with self.subTest(x=x, y=y):
                self.assertEqual(calculator.multiply(x, y), expected)

    def test_add_three(self):
        for x, y, z, expected in [(2, 3, 5, 10), (5, 0, -1, 4), (-1, -1, -1, -3), (-1, -1, 100, 98)]:
            with self.subTest(x=x, y=y, z=z):
                self.assertEqual(calculator.add_three(x, y, z), expected)


class TestDivide(unittest.TestCase):

    def test_divide(self):
        for x, y, expected in [(6, 3, 2.0), (7, 2, 3.5), (-9, 3, -3.0), (0, 5, 0.0), (1, 3, 1 / 3)]:
            with self.subTest(x=x, y=y):
                self.assertAlmostEqual(calculator.divide(x, y), expected)

    def test_divide_by_zero_raises(self):
        for zero in [0, 0.0, -0.0]:
            with self.subTest(zero=zero):
                with self.assertRaisesRegex(ValueError, "cannot be zero"):
                    calculator.divide(1, zero)


class TestPower(unittest.TestCase):

    def test_power(self):
        cases = [(2, 3, 8), (2, 0, 1), (0, 0, 1), (2, -1, 0.5), (-8, 3, -512), (-8, 2.0, 64.0), (9, 0.5, 3.0)]
        for x, y, expected in cases:
            with self.subTest(x=x, y=y):
                self.assertAlmostEqual(calculator.power(x, y), expected)

    def test_power_zero_to_negative_raises(self):
        with self.assertRaisesRegex(ValueError, "negative power"):
            calculator.power(0, -1)

    def test_power_complex_result_raises(self):
        # In plain Python, (-8) ** (1/3) returns a complex number
        with self.assertRaisesRegex(ValueError, "no real result"):
            calculator.power(-8, 1 / 3)

    def test_power_overflow_raises(self):
        with self.assertRaisesRegex(ValueError, "too large"):
            calculator.power(10.0, 400)


class TestModulo(unittest.TestCase):

    def test_modulo(self):
        # Result takes the sign of the divisor
        for x, y, expected in [(7, 3, 1), (6, 3, 0), (-7, 3, 2), (7, -3, -2), (5.5, 2, 1.5)]:
            with self.subTest(x=x, y=y):
                self.assertAlmostEqual(calculator.modulo(x, y), expected)

    def test_modulo_by_zero_raises(self):
        with self.assertRaisesRegex(ValueError, "cannot be zero"):
            calculator.modulo(7, 0)


class TestAverage(unittest.TestCase):

    def test_average(self):
        for x, y, z, expected in [(1, 2, 3, 2.0), (1, 2, 2, 5 / 3), (-3, 0, 3, 0.0), (2.5, 2.5, 2.5, 2.5)]:
            with self.subTest(x=x, y=y, z=z):
                self.assertAlmostEqual(calculator.average(x, y, z), expected)


if __name__ == '__main__':
    unittest.main()

import math

import pytest
from src import calculator

INVALID_INPUTS = ["2", None, True, False, math.nan, math.inf, -math.inf, [1]]

TWO_ARG_FUNCS = [
    calculator.add,
    calculator.subtract,
    calculator.multiply,
    calculator.divide,
    calculator.power,
    calculator.modulo,
]
THREE_ARG_FUNCS = [calculator.add_three, calculator.average]



@pytest.mark.parametrize("value", [0, -1, 2.5, -0.0, 10**20])
def test_is_num_accepts_finite_numbers(value):
    assert calculator.is_num(value)

@pytest.mark.parametrize("value", INVALID_INPUTS)
def test_is_num_rejects_invalid(value):
    assert not calculator.is_num(value)

@pytest.mark.parametrize("func", TWO_ARG_FUNCS)
@pytest.mark.parametrize("bad", INVALID_INPUTS)
def test_two_arg_funcs_reject_invalid(func, bad):
    with pytest.raises(ValueError):
        func(bad, 1)
    with pytest.raises(ValueError):
        func(1, bad)

@pytest.mark.parametrize("func", THREE_ARG_FUNCS)
@pytest.mark.parametrize("bad", INVALID_INPUTS)
def test_three_arg_funcs_reject_invalid(func, bad):
    for args in [(bad, 1, 1), (1, bad, 1), (1, 1, bad)]:
        with pytest.raises(ValueError):
            func(*args)



@pytest.mark.parametrize("x, y, expected", [
    (2, 3, 5),
    (5, 0, 5),
    (-1, 1, 0),
    (-1, -1, -2),
])
def test_add(x, y, expected):
    assert calculator.add(x, y) == expected

def test_add_floats():
    assert calculator.add(0.1, 0.2) == pytest.approx(0.3)

@pytest.mark.parametrize("x, y, expected", [
    (2, 3, -1),
    (5, 0, 5),
    (-1, 1, -2),
    (-1, -1, 0),
])
def test_subtract(x, y, expected):
    assert calculator.subtract(x, y) == expected

@pytest.mark.parametrize("x, y, expected", [
    (2, 3, 6),
    (5, 0, 0),
    (-1, 1, -1),
    (-1, -1, 1),
    (2.5, 4, 10.0),
])
def test_multiply(x, y, expected):
    assert calculator.multiply(x, y) == expected

@pytest.mark.parametrize("x, y, z, expected", [
    (2, 3, 5, 10),
    (5, 0, -1, 4),
    (-1, -1, -1, -3),
    (-1, -1, 100, 98),
])
def test_add_three(x, y, z, expected):
    assert calculator.add_three(x, y, z) == expected



@pytest.mark.parametrize("x, y, expected", [
    (6, 3, 2.0),
    (7, 2, 3.5),
    (-9, 3, -3.0),
    (0, 5, 0.0),
    (1, 3, 1 / 3),
])
def test_divide(x, y, expected):
    assert calculator.divide(x, y) == pytest.approx(expected)

@pytest.mark.parametrize("zero", [0, 0.0, -0.0])
def test_divide_by_zero_raises(zero):
    with pytest.raises(ValueError, match="cannot be zero"):
        calculator.divide(1, zero)



@pytest.mark.parametrize("x, y, expected", [
    (2, 3, 8),
    (2, 0, 1),
    (0, 0, 1),
    (2, -1, 0.5),
    (-8, 3, -512),
    (-8, 2.0, 64.0),
    (9, 0.5, 3.0),
])
def test_power(x, y, expected):
    assert calculator.power(x, y) == pytest.approx(expected)

def test_power_zero_to_negative_raises():
    with pytest.raises(ValueError, match="negative power"):
        calculator.power(0, -1)

def test_power_complex_result_raises():
    # In plain Python, (-8) ** (1/3) returns a complex number
    with pytest.raises(ValueError, match="no real result"):
        calculator.power(-8, 1 / 3)

def test_power_overflow_raises():
    with pytest.raises(ValueError, match="too large"):
        calculator.power(10.0, 400)



@pytest.mark.parametrize("x, y, expected", [
    (7, 3, 1),
    (6, 3, 0),
    (-7, 3, 2),    # result takes the sign of the divisor
    (7, -3, -2),
    (5.5, 2, 1.5),
])
def test_modulo(x, y, expected):
    assert calculator.modulo(x, y) == pytest.approx(expected)

def test_modulo_by_zero_raises():
    with pytest.raises(ValueError, match="cannot be zero"):
        calculator.modulo(7, 0)



@pytest.mark.parametrize("x, y, z, expected", [
    (1, 2, 3, 2.0),
    (1, 2, 2, 5 / 3),
    (-3, 0, 3, 0.0),
    (2.5, 2.5, 2.5, 2.5),
])
def test_average(x, y, z, expected):
    assert calculator.average(x, y, z) == pytest.approx(expected)

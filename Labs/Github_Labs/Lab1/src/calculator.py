import math


def is_num(value):
    """
    Checks if the input value is a finite number (int or float).
    Booleans, NaN and infinity are not accepted.
    Args:
        value: The value to check.
    Returns:
        bool: True if the value is a finite number, False otherwise.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)

def val_num(*values):
    """
    Validates that all inputs are finite numbers.
    Args:
        *values: The values to validate.
    Raises:
        ValueError: If any value is not a finite number.
    """
    if not all(is_num(v) for v in values):
        raise ValueError("All inputs must be finite numbers.")

def add(x, y):
    """
    Adds two numbers together.
    Args:
        x (int/float): First number.
        y (int/float): Second number.
    Returns:
        int/float: Sum of x and y.
    Raises:
        ValueError: If x or y is not a number.
    """
    val_num(x, y)
    return x + y

def subtract(x, y):
    """
    Subtracts two numbers.
    Args:
        x (int/float): First number.
        y (int/float): Second number.
    Returns:
        int/float: Difference of x and y.
    Raises:
        ValueError: If x or y is not a number.
    """
    val_num(x, y)
    return x - y

def multiply(x, y):
    """
    Multiplies two numbers together.
    Args:
        x (int/float): First number.
        y (int/float): Second number.
    Returns:
        int/float: Product of x and y.
    Raises:
        ValueError: If x or y is not a number.
    """
    val_num(x, y)
    return x * y

def add_three(x, y, z):
    """
    Adds three numbers together.
    Args:
        x (int/float): First number.
        y (int/float): Second number.
        z (int/float): Third number.
    Returns:
        int/float: Sum of x, y and z.
    Raises:
        ValueError: If x, y or z is not a number.
    """
    val_num(x, y, z)
    return x + y + z

def divide(x, y):
    """
    Divides two numbers.
    Args:
        x (int/float): Numerator.
        y (int/float): Denominator.
    Returns:
        float: Result of division x / y.
    Raises:
        ValueError: If x or y is not a number or if y is zero.
    """
    val_num(x, y)
    if y == 0:
        raise ValueError("Denominator cannot be zero.")
    return x / y

def power(x, y):
    """
    Raises a number to the power of another number.
    Args:
        x (int/float): Base number.
        y (int/float): Exponent.
    Returns:
        int/float: Result of x raised to the power of y.
    Raises:
        ValueError: If x or y is not a number, if x is zero and y is negative,
            if x is negative and y is not a whole number (complex result),
            or if the result is too large to represent.
    """
    val_num(x, y)
    if x == 0 and y < 0:
        raise ValueError("Zero cannot be raised to a negative power.")
    if x < 0 and not float(y).is_integer():
        raise ValueError("Negative base with a fractional exponent has no real result.")
    try:
        return x ** y
    except OverflowError:
        raise ValueError("Result is too large to represent.")

def modulo(x, y):
    """
    Computes the remainder of the division of two numbers.
    Args:
        x (int/float): Dividend.
        y (int/float): Divisor.
    Returns:
        int/float: Remainder of x divided by y (takes the sign of y).
    Raises:
        ValueError: If x or y is not a number or if y is zero.
    """
    val_num(x, y)
    if y == 0:
        raise ValueError("Divisor cannot be zero.")
    return x % y

def average(x, y, z):
    """
    Computes the average of three numbers.
    Args:
        x (int/float): First number.
        y (int/float): Second number.
        z (int/float): Third number.
    Returns:
        float: Average of x, y and z.
    Raises:
        ValueError: If x, y or z is not a number.
    """
    val_num(x, y, z)
    return (x + y + z) / 3

"""
Sample unit tests demonstrating basic test cases.
"""
import pytest
from datetime import datetime

def test_string_operations():
    """Test basic string operations."""
    text = "Hello, World!"
    assert len(text) == 13
    assert text.upper() == "HELLO, WORLD!"
    assert text.lower() == "hello, world!"
    assert text.split(",") == ["Hello", " World!"]

def test_numeric_operations():
    """Test basic numeric operations."""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 4 == 12
    assert 15 / 3 == 5
    assert 2 ** 3 == 8

def test_list_operations():
    """Test list operations."""
    numbers = [1, 2, 3, 4, 5]
    assert len(numbers) == 5
    assert sum(numbers) == 15
    assert max(numbers) == 5
    assert min(numbers) == 1
    assert sorted(numbers, reverse=True) == [5, 4, 3, 2, 1]

def test_datetime_operations():
    """Test datetime operations."""
    now = datetime.now()
    assert isinstance(now, datetime)
    assert now.year >= 2024
    assert 1 <= now.month <= 12
    assert 1 <= now.day <= 31

@pytest.mark.parametrize("input_value,expected", [
    (2, 4),
    (3, 9),
    (4, 16),
    (5, 25),
])
def test_square_numbers(input_value, expected):
    """Test squaring numbers with parameterized test."""
    assert input_value ** 2 == expected 
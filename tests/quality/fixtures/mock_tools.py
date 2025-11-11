#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test file to demonstrate quality tools working on actual Python code.

This file contains various patterns that quality tools would analyze:
- Functions with and without docstrings
- Simple and complex functions
- Security patterns
- Different levels of test coverage"""

from collections.abc import Iterable
import subprocess


def well_documented_function(param1: str, param2: int) -> str:
    """A well-documented function for testing documentation coverage.

    This function demonstrates proper documentation practices with
    detailed parameter descriptions and return value information.

    Args:
        param1: A string parameter for demonstration
        param2: An integer parameter for calculations

    Returns:
        A formatted string combining the parameters

    Example:
        >>> well_documented_function("test", 42)
        'test: 42'
    """
    return f"{param1}: {param2}"


def undocumented_function(x: int, y: int) -> int:
    # This function has no docstring - should be flagged by documentation tools
    return x + y


def simple_function() -> str:
    """Simple function with low complexity."""
    return "Hello, World!"


def complex_function(data: Iterable[object]) -> list[str | int]:
    """Function with higher complexity for testing."""
    result: list[str | int] = []
    for item in data:
        if item is None:
            continue
        elif isinstance(item, str):
            if item.startswith("prefix"):
                result.append(item.upper())
            elif item.endswith("suffix"):
                result.append(item.lower())
            else:
                result.append(item.title())
        elif isinstance(item, int):
            if item > 0:
                if item % 2 == 0:
                    result.append(item * 2)
                else:
                    result.append(item * 3)
            else:
                result.append(0)
        else:
            result.append(str(item))
    return result


def potentially_insecure_function(user_input: str) -> str:
    """Function that might trigger security warnings."""
    # This should trigger a security warning about shell injection
    command = f"echo {user_input}"
    # Note: This is intentionally insecure for demonstration
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout


def function_with_assert() -> int:
    """Function with assert statement."""
    value = 42
    assert value > 0  # This might trigger B101 in bandit
    return value


class WellDocumentedClass:
    """A well-documented class for testing.

    This class demonstrates proper class documentation
    with detailed descriptions of its purpose and usage.
    """

    def __init__(self, name: str) -> None:
        """Initialize the class.

        Args:
            name: The name for this instance
        """
        self.name = name

    def documented_method(self) -> str:
        """A documented method.

        Returns:
            The name of this instance
        """
        return self.name


class UndocumentedClass:
    def __init__(self, value: int) -> None:
        self.value = value

    def undocumented_method(self) -> int:
        return self.value * 2


if __name__ == "__main__":
    # Test the functions
    print("Testing quality demonstration functions...")

    # Test simple functions
    print("Simple function:", simple_function())
    print("Well documented:", well_documented_function("test", 123))
    print("Undocumented:", undocumented_function(10, 20))

    # Test complex function
    test_data = ["prefix_test", "test_suffix", "normal", 4, 5, 0, None, 3.14]
    print("Complex function:", complex_function(test_data))

    # Test classes
    doc_class = WellDocumentedClass("documented")
    print("Documented class:", doc_class.documented_method())

    undoc_class = UndocumentedClass(42)
    print("Undocumented class:", undoc_class.undocumented_method())

    # Test function with assert
    print("Assert function:", function_with_assert())

    print("\nThis file can be analyzed by quality tools to demonstrate:")
    print("- Documentation coverage (some functions/classes documented, others not)")
    print("- Code complexity (simple vs complex functions)")
    print("- Security issues (shell injection, assert usage)")
    print("- Test coverage (if run with coverage tracking)")

# 🧪✅🔚

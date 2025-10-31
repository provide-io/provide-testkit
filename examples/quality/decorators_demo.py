#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Demonstration of quality decorators functionality.

This script shows how the quality decorators work by applying them to test functions
and demonstrating both passing and failing scenarios."""

from __future__ import annotations

import time

from provide.testkit.quality.decorators import performance_gate, quality_check


@performance_gate(max_memory_mb=100.0, max_execution_time=1.0)
def fast_function():
    """A fast function that should pass performance requirements."""
    # Simple computation that's fast and low memory
    result = sum(range(1000))
    return result


@performance_gate(max_memory_mb=1.0, max_execution_time=0.001)  # Very strict
def potentially_slow_function():
    """A function that might fail strict performance requirements."""
    # This might be too slow for the 0.001s requirement
    time.sleep(0.01)  # 10ms sleep
    result = sum(range(10000))
    return result


@quality_check(performance={"max_memory_mb": 50.0, "max_execution_time": 0.5})
def comprehensive_test_function():
    """A function with comprehensive quality requirements."""
    # Do some work
    data = list(range(5000))
    result = sum(x * x for x in data)
    return result


def demonstrate_performance_gates():
    """Demonstrate performance gate functionality."""
    print("🏃 Performance Gates Demonstration")
    print("=" * 50)

    # Test 1: Fast function (should pass)
    print("Test 1: Fast function with reasonable limits")
    try:
        result = fast_function()
    except AssertionError as e:
        print(f"  ❌ FAILED - {e}")

    print()

    # Test 2: Strict limits (might fail)
    print("Test 2: Function with very strict limits")
    try:
        result = potentially_slow_function()
    except AssertionError as e:
        print(f"  ❌ FAILED - {e}")

    print()

    # Test 3: Comprehensive quality check
    print("Test 3: Comprehensive quality check")
    try:
        result = comprehensive_test_function()
    except AssertionError as e:
        print(f"  ❌ FAILED - {e}")

    print()


def demonstrate_manual_profiling():
    """Demonstrate manual profiling without decorators."""
    print("=" * 50)

    from provide.testkit.quality.profiling.profiler import PerformanceProfiler

    profiler = PerformanceProfiler({"max_memory_mb": 100.0, "max_execution_time": 1.0})

    def example_function():
        """Example function to profile."""
        data = list(range(10000))
        result = sum(x**2 for x in data if x % 2 == 0)
        return result

    print("Profiling example function...")
    result = profiler.profile_function(example_function)

    if result.score is not None:
        print(f"Score: {result.score:.1f}%")
    else:
        print("Score: N/A")

    memory_data = result.details.get("memory", {})
    cpu_data = result.details.get("cpu", {})

    if memory_data:
        print(f"Peak Memory: {memory_data.get('peak_memory_mb', 0):.3f} MB")

    if cpu_data:
        print(f"Execution Time: {cpu_data.get('execution_time', 0):.4f} seconds")

    print()


def main():
    """Main demonstration function."""
    print("🚀 Quality Decorators Demonstration")
    print("=" * 60)
    print()

    # Demonstrate performance gates
    demonstrate_performance_gates()

    # Demonstrate manual profiling
    demonstrate_manual_profiling()

    print("🎉 Quality Decorators Demonstration Complete!")
    print()
    print("   • Performance gate decorators")
    print("   • Quality check decorators")
    print("   • Manual profiling interface")
    print("   • Performance requirement enforcement")


if __name__ == "__main__":
    main()

# 🧪✅🔚

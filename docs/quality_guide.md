# Quality Module Guide

The quality module provides comprehensive code quality analysis tools for the provide ecosystem. It integrates multiple quality tools including coverage analysis, security scanning, complexity analysis, documentation coverage, and performance profiling.

## Features

- **Coverage Analysis**: Code coverage tracking with coverage.py
- **Security Scanning**: Vulnerability detection with bandit
- **Complexity Analysis**: Code complexity metrics with radon
- **Documentation Coverage**: Docstring coverage with interrogate
- **Performance Profiling**: Memory and CPU profiling with memray/cProfile
- **Quality Decorators**: Easy-to-use decorators for quality enforcement
- **Quality Gates**: Configurable thresholds for quality requirements
- **Artifact Management**: Organized storage and cleanup of analysis results
- **CLI Interface**: Command-line tools for quality analysis

## Installation

The quality module has optional dependencies for different tools:

```bash
# Install with all quality tools
pip install provide-testkit[quality]

# Install specific tool sets
pip install provide-testkit[coverage,security,complexity]

# Install for development with all tools
pip install provide-testkit[all]
```

## Quick Start

### Using Quality Fixtures

```python
def test_with_coverage(coverage_tracker):
    """Test using coverage fixture."""
    coverage_tracker.start()

    # Your test code here
    result = my_function()

    coverage_tracker.stop()
    analysis = coverage_tracker.analyze(Path("./src"))

    assert analysis["passed"]
    assert analysis["coverage_percentage"] >= 80.0
```

### Using Quality Decorators

```python
from provide.testkit.quality import quality_check, coverage_gate

@coverage_gate(80.0)
def test_coverage_requirement():
    """This test requires 80% coverage."""
    # Test implementation
    pass

@quality_check(
    coverage=80.0,
    security=True,
    complexity={"max_complexity": 10}
)
def test_comprehensive_quality():
    """Multi-dimensional quality check."""
    # Test implementation
    pass
```

### Using Quality Runner

```python
from provide.testkit.quality.runner import QualityRunner

runner = QualityRunner()

# Run specific tools
results = runner.run_tools(
    Path("./src"),
    ["coverage", "security", "complexity"]
)

# Run with quality gates
gates = {
    "coverage": 80.0,
    "security": 90.0,
    "complexity": {"max_complexity": 10}
}

gate_results = runner.run_with_gates(Path("./src"), gates)
```

## Quality Tools

### Coverage Analysis

Tracks code coverage using coverage.py:

```python
from provide.testkit.quality.coverage import CoverageTracker

tracker = CoverageTracker({
    "min_coverage": 85.0,
    "generate_html": True,
    "exclude": ["*/tests/*"]
})

result = tracker.analyze(Path("./src"))
```

**Configuration Options:**
- `min_coverage`: Minimum coverage percentage (default: 80.0)
- `generate_html`: Generate HTML coverage report (default: False)
- `generate_xml`: Generate XML coverage report (default: False)
- `exclude`: File patterns to exclude from coverage

### Security Scanning

Scans for security vulnerabilities using bandit:

```python
from provide.testkit.quality.security import SecurityScanner

scanner = SecurityScanner({
    "min_score": 95.0,
    "ignore_issues": ["B101", "B601"]
})

result = scanner.analyze(Path("./src"))
```

**Configuration Options:**
- `min_score`: Minimum security score (default: 90.0)
- `ignore_issues`: List of bandit issue IDs to ignore
- `severity_weights`: Custom weights for different severity levels

### Complexity Analysis

Analyzes code complexity using radon:

```python
from provide.testkit.quality.complexity import ComplexityAnalyzer

analyzer = ComplexityAnalyzer({
    "max_complexity": 10,
    "min_grade": "B",
    "exclude": ["*/legacy/*"]
})

result = analyzer.analyze(Path("./src"))
```

**Configuration Options:**
- `max_complexity`: Maximum allowed complexity (default: 20)
- `min_grade`: Minimum complexity grade (A, B, C, D, F)
- `min_score`: Minimum complexity score (default: 70.0)
- `exclude`: File patterns to exclude

### Documentation Coverage

Checks documentation coverage using interrogate:

```python
from provide.testkit.quality.documentation import DocumentationChecker

checker = DocumentationChecker({
    "min_coverage": 80.0,
    "min_grade": "B",
    "ignore_init_method": True
})

result = checker.analyze(Path("./src"))
```

**Configuration Options:**
- `min_coverage`: Minimum documentation coverage (default: 80.0)
- `min_grade`: Minimum documentation grade
- `ignore_init_method`: Ignore __init__ methods (default: True)
- `ignore_magic`: Ignore magic methods (default: True)

### Performance Profiling

Profiles performance using memray and cProfile:

```python
from provide.testkit.quality.profiling import PerformanceProfiler

profiler = PerformanceProfiler({
    "max_memory_mb": 100.0,
    "max_execution_time": 1.0,
    "use_memray": True
})

result = profiler.profile_function(my_function, *args)
```

**Configuration Options:**
- `max_memory_mb`: Maximum memory usage in MB
- `max_execution_time`: Maximum execution time in seconds
- `use_memray`: Use memray for memory profiling (default: True if available)
- `profile_memory`: Enable memory profiling (default: True)
- `profile_cpu`: Enable CPU profiling (default: True)

## Quality Decorators

### Basic Decorators

```python
from provide.testkit.quality import (
    coverage_gate, security_gate, complexity_gate,
    documentation_gate, performance_gate
)

@coverage_gate(80.0)
def test_coverage():
    pass

@security_gate(95.0)
def test_security():
    pass

@complexity_gate(max_complexity=10, min_grade="B")
def test_complexity():
    pass

@documentation_gate(min_coverage=80.0)
def test_documentation():
    pass

@performance_gate(max_memory_mb=50.0, max_execution_time=1.0)
def test_performance():
    return expensive_computation()
```

### Comprehensive Quality Decorator

```python
@quality_check(
    coverage=80.0,
    security=True,
    complexity={"max_complexity": 10, "min_grade": "B"},
    documentation={"min_coverage": 80.0},
    performance={"max_memory_mb": 100.0}
)
def test_all_quality_aspects():
    """This test enforces multiple quality requirements."""
    pass
```

## Quality Gates

Quality gates define thresholds that must be met for analysis to pass:

```python
gates = {
    # Simple percentage requirement
    "coverage": 80.0,

    # Boolean requirement (use default thresholds)
    "security": True,

    # Complex requirements
    "complexity": {
        "max_complexity": 10,
        "min_grade": "B",
        "min_score": 85.0
    },

    # String grade requirement
    "documentation": "B"
}

runner = QualityRunner()
results = runner.run_with_gates(Path("./src"), gates)

if results.passed:
    print("✅ All quality gates passed!")
else:
    print("❌ Quality gates failed!")
```

## Artifact Management

The quality module provides comprehensive artifact management:

```python
from provide.testkit.quality.artifacts import ArtifactManager

# Create artifact manager
manager = ArtifactManager(".quality-artifacts")

# Create organized directories
session_dir = manager.create_session_dir("coverage")
timestamped_dir = manager.create_timestamped_dir("security")

# Organize artifacts from results
manager.organize_artifacts(result, target_dir)

# Create summary reports
summary_path = manager.create_summary_report(results)

# Generate artifact index
index_path = manager.generate_index()

# Check disk usage
usage = manager.get_disk_usage()
print(f"Artifacts use {usage['total_mb']:.2f} MB")

# Cleanup old artifacts
manager.cleanup_old_artifacts(keep_count=5)

# Export artifacts
export_path = manager.export_artifacts("export.tar.gz", compress=True)
```

## CLI Interface

The quality module provides a comprehensive CLI:

```bash
# Basic analysis
provide-testkit quality analyze ./src

# Specific tools
provide-testkit quality analyze ./src --tool coverage --tool security

# With configuration
provide-testkit quality analyze ./src --config quality_config.json

# Quality gates
provide-testkit quality gates ./src --coverage 80 --security 90

# Individual tools
provide-testkit quality coverage ./src --min-coverage 85 --html
provide-testkit quality security ./src --min-score 95
provide-testkit quality complexity ./src --max-complexity 10
```

## Configuration

### Configuration Files

Quality tools can be configured using JSON configuration files:

```json
{
  "coverage": {
    "min_coverage": 85.0,
    "generate_html": true,
    "exclude": ["*/tests/*", "*/migrations/*"]
  },
  "security": {
    "min_score": 95.0,
    "ignore_issues": ["B101", "B601"]
  },
  "complexity": {
    "max_complexity": 8,
    "min_grade": "A",
    "exclude": ["*/legacy/*"]
  },
  "documentation": {
    "min_coverage": 90.0,
    "min_grade": "A",
    "ignore_init_method": true
  }
}
```

### Environment Variables

Some settings can be controlled via environment variables:

- `QUALITY_ARTIFACT_DIR`: Default artifact directory
- `QUALITY_FAIL_FAST`: Stop on first failure
- `QUALITY_VERBOSE`: Enable verbose output

## Integration with pytest

### Fixtures

The quality module provides several pytest fixtures:

```python
def test_coverage(coverage_tracker):
    """Use coverage tracking fixture."""
    pass

def test_security(security_scanner):
    """Use security scanning fixture."""
    pass

def test_complexity(complexity_analyzer):
    """Use complexity analysis fixture."""
    pass

def test_documentation(documentation_checker):
    """Use documentation coverage fixture."""
    pass

def test_profiling(profiling_fixture):
    """Use performance profiling fixture."""
    pass
```

### Configuration Fixtures

```python
def test_with_config(coverage_config, security_config):
    """Use configuration fixtures."""
    pass
```

### Strict Fixtures

```python
def test_strict_requirements(
    coverage_checker_strict,
    security_scanner_strict,
    complexity_analyzer_strict
):
    """Use strict quality requirements."""
    pass
```

## Best Practices

### 1. Start with Basic Requirements

Begin with reasonable quality thresholds and gradually increase them:

```python
# Start here
gates = {
    "coverage": 60.0,
    "security": True,
    "complexity": "C"
}

# Progress to here
gates = {
    "coverage": 80.0,
    "security": 95.0,
    "complexity": {"max_complexity": 10, "min_grade": "B"}
}
```

### 2. Use Quality Decorators for Important Tests

Apply quality decorators to critical test functions:

```python
@quality_check(coverage=90.0, security=True)
def test_critical_security_feature():
    """Critical security test with high quality requirements."""
    pass
```

### 3. Configure Tool Exclusions

Exclude appropriate files from analysis:

```python
config = {
    "coverage": {
        "exclude": ["*/tests/*", "*/migrations/*", "*/vendor/*"]
    },
    "complexity": {
        "exclude": ["*/legacy/*", "*/generated/*"]
    }
}
```

### 4. Use Artifact Management

Organize and clean up artifacts regularly:

```python
# In CI/CD pipeline
manager = ArtifactManager()
manager.cleanup_old_artifacts(keep_count=10)
manager.export_artifacts("quality_report.tar.gz")
```

### 5. Gradual Quality Improvement

Implement quality gates incrementally:

```python
# Week 1: Basic requirements
@coverage_gate(50.0)

# Week 2: Increase coverage
@coverage_gate(65.0)

# Week 3: Add security
@quality_check(coverage=65.0, security=True)

# Week 4: Add complexity
@quality_check(coverage=75.0, security=True, complexity="C")
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Install optional dependencies:
   ```bash
   pip install provide-testkit[quality]
   ```

2. **Permission Errors**: Ensure write access to artifact directories:
   ```python
   manager = ArtifactManager("/tmp/quality-artifacts")
   ```

3. **Memory Issues**: Configure profiling limits:
   ```python
   config = {"max_memory_mb": 1000}  # Increase limit
   ```

4. **Performance Issues**: Use sampling for large codebases:
   ```python
   config = {"sample_rate": 0.1}  # Analyze 10% of files
   ```

### Debug Mode

Enable debug output for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use verbose mode
runner = QualityRunner(verbose=True)
```

## Examples

See `examples/quality_examples.py` for comprehensive examples demonstrating all features of the quality module.

## API Reference

For detailed API documentation, see the docstrings in each module:

- `provide.testkit.quality.base` - Core interfaces and base classes
- `provide.testkit.quality.runner` - Quality orchestration
- `provide.testkit.quality.coverage` - Coverage analysis
- `provide.testkit.quality.security` - Security scanning
- `provide.testkit.quality.complexity` - Complexity analysis
- `provide.testkit.quality.documentation` - Documentation coverage
- `provide.testkit.quality.profiling` - Performance profiling
- `provide.testkit.quality.decorators` - Quality decorators
- `provide.testkit.quality.artifacts` - Artifact management
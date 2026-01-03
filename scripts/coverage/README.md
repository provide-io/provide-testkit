# Coverage Testing Scripts

This directory contains scripts for running pytest with coverage across multiple packages in parallel and analyzing the results.

## Scripts

### `run_tests.sh`

Runs pytest with branch coverage for multiple packages in parallel, saving individual logs for each package.

**Usage:**
```bash
./run_tests.sh [LOG_DIR]
```

**Arguments:**
- `LOG_DIR` - Optional output directory for logs (default: `/tmp/pytest-logs`)

**Features:**
- Parallel test execution across multiple packages
- Branch coverage collection with `pytest-cov`
- Individual log files for each package
- Automatic environment setup using `uv` (creates `.venv` if needed)
- Works with `pytest-xdist` for parallel test execution within each package

**Configuration:**

Edit the `packages` array in the script to specify your packages:

```bash
packages=(
    "package-name:/absolute/path/to/package"
    "another-package:/absolute/path/to/another"
)
```

**Example:**
```bash
# Run with default log directory
./run_tests.sh

# Run with custom log directory
./run_tests.sh /path/to/my/logs

# View results while tests are running
tail -f /tmp/pytest-logs/package-name.log
```

### `analyze_results.py`

Parses pytest log files and generates a comprehensive coverage and test results report.

**Usage:**
```bash
python3 analyze_results.py [LOG_DIR]
```

**Arguments:**
- `LOG_DIR` - Directory containing `.log` files (default: `/tmp/pytest-logs`)

**Features:**
- Parses test counts (passed/failed/skipped)
- Extracts coverage percentages (line and branch coverage)
- Identifies failed tests with file paths
- Generates summary statistics
- Highlights high/low performers
- Identifies packages with issues

**Output:**
- Console: Formatted report with summary table and observations
- File: `REPORT.txt` in the log directory

**Example:**
```bash
# Analyze default log directory
python3 analyze_results.py

# Analyze custom log directory
python3 analyze_results.py /path/to/my/logs

# Save report to file
python3 analyze_results.py > my-coverage-report.txt
```

## Complete Workflow

Here's a typical workflow for running tests across all packages and analyzing results:

```bash
# 1. Navigate to the scripts directory
cd /path/to/provide-io/provide-testkit/scripts/coverage

# 2. Run all tests in parallel (takes a few minutes)
./run_tests.sh

# 3. Wait for completion, then analyze results
python3 analyze_results.py

# 4. View the detailed report
cat /tmp/pytest-logs/REPORT.txt

# 5. Check individual package logs if needed
cat /tmp/pytest-logs/package-name.log
```

## Report Format

The report includes:

### Summary Table
```
Package                   Status       Tests           Pass Rate    Coverage     Time
flavorpack                ✗ FAILED     992P/34F/3S     96.4%        82.17%       93.71s
pyvider-rpcplugin         ✓ PASSED     553P/0F/0S      100.0%       94.2%        101.02s
```

### Overall Statistics
- Total packages tested
- Total test counts (passed/failed/skipped)
- Overall pass rate
- Average coverage

### Detailed Results
Per-package breakdown including:
- Test counts and status
- Coverage percentages
- Execution time
- Failed test names and file paths

### Observations
- Packages with failures
- Packages with low coverage (<70%)
- High-performing packages (passing + ≥80% coverage)

## Requirements

**For `run_tests.sh`:**
- Bash shell
- Python 3.11+
- uv package manager
- pytest with pytest-cov plugin
- pytest-xdist (for parallel execution)
- coverage.py

**For `analyze_results.py`:**
- Python 3.11+

## Customization

### Adding/Removing Packages

Edit the `packages` array in `run_tests.sh`:

```bash
packages=(
    "my-package:/path/to/my-package"
    "another-package:/path/to/another"
)
```

### Changing Coverage Thresholds

Edit the observation thresholds in `analyze_results.py`:

```python
# Low coverage threshold (line 221)
low_cov = [r for r in packages_with_tests if (r.total_coverage or r.coverage_line or 100) < 70]

# High performer threshold (line 227)
high_perf = [r for r in packages_with_tests
             if r.status == "PASSED"
             and (r.total_coverage or r.coverage_line or 0) >= 80]
```

## Tips

- **Parallel Execution**: Tests run in parallel across packages. Within each package, `pytest -n auto` also parallelizes tests.
- **Log Files**: Each package gets its own log file for easier debugging.
- **Coverage Reports**: Coverage data is combined automatically using `coverage combine`.
- **Environment Setup**: Uses `uv sync` to ensure dependencies are installed, then `uv run` to execute tests in the package's virtual environment.
- **Interrupting**: Press Ctrl+C to stop all running tests (background processes will be terminated).

## Troubleshooting

**Tests not running for a package:**
- Check if the package path is correct
- Verify that the package has a `pyproject.toml` with dependencies
- Check the individual log file for errors
- Ensure `uv` is installed and available

**Coverage not showing:**
- Ensure pytest-cov is listed in the package's dependencies
- Check that the package name format matches the module structure (e.g., `my-package` → `my.package`)

**UNKNOWN status in report:**
- Package may not have tests
- Tests may have failed to start (check log file)
- `uv sync` may have failed (check log file for errors)

## Related Documentation

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [coverage.py documentation](https://coverage.readthedocs.io/)

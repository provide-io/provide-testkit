#!/bin/bash
#
# run_tests.sh - Run pytest with coverage for multiple packages in parallel
#
# This script runs pytest with branch coverage across multiple Python packages
# in parallel, saving individual logs for each package. It's designed for
# monorepo or multi-package testing scenarios.
#
# Usage:
#   ./run_tests.sh [LOG_DIR]
#
# Arguments:
#   LOG_DIR - Optional output directory for logs (default: /tmp/pytest-logs)
#
# Configuration:
#   Edit the 'packages' array below to specify your packages and paths
#
# Based on the pattern from pyvider-cty/run-coverage.sh

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================

# Output directory for logs (can be overridden via command line)
LOG_DIR="${1:-/tmp/pytest-logs}"
mkdir -p "$LOG_DIR"

# List of packages with their paths (package:path format)
# Format: "package-name:/absolute/path/to/package"
#
# To customize for your projects, edit this array:
packages=(
    "flavorpack:/REDACTED_ABS_PATH"
    "plating:/REDACTED_ABS_PATH"
    "provide-foundation:/REDACTED_ABS_PATH"
    "provide-testkit:/REDACTED_ABS_PATH"
    "pyvider:/REDACTED_ABS_PATH"
    "pyvider-components:/REDACTED_ABS_PATH"
    "pyvider-cty:/REDACTED_ABS_PATH"
    "pyvider-hcl:/REDACTED_ABS_PATH"
    "pyvider-rpcplugin:/REDACTED_ABS_PATH"
    "supsrc:/REDACTED_ABS_PATH"
    "tofusoup:/REDACTED_ABS_PATH"
    "wrknv:/REDACTED_ABS_PATH"
)

# ============================================================================
# SCRIPT IMPLEMENTATION (no need to edit below this line)
# ============================================================================

# Function to run tests for a single package
run_package_tests() {
    local package=$1
    local path=$2
    local log_file="$LOG_DIR/${package}.log"

    echo "[$package] Starting tests..." > "$log_file"

    cd "$path" 2>>"$log_file" || {
        echo "[$package] ERROR: Cannot change to directory $path" >> "$log_file"
        return 1
    }

    # Clean up old coverage data
    rm -f .coverage .coverage.* 2>>"$log_file"

    # Determine package name for coverage (convert package-name to package.name)
    local cov_package=$(echo "$package" | sed 's/-/./g')

    # Ensure dependencies are installed
    # Uses uv to run pytest in the package's virtual environment
    # No need to manually activate venv or source env.sh
    if [ ! -d ".venv" ]; then
        echo "[$package] Creating virtual environment..." >> "$log_file"
        uv sync >> "$log_file" 2>&1 || {
            echo "[$package] ERROR: Failed to sync dependencies" >> "$log_file"
            return 1
        }
    fi

    # Run tests with coverage using uv run (automatically uses .venv)
    echo "[$package] Running pytest with coverage..." >> "$log_file"
    uv run pytest \
        --cov-branch \
        --cov="$cov_package" \
        -n auto \
        --cov-report= \
        -v \
        2>&1 | tee -a "$log_file" || true

    # Combine coverage data
    if [ -f ".coverage" ] || ls .coverage.* 1> /dev/null 2>&1; then
        echo "[$package] Combining coverage data..." >> "$log_file"
        uv run coverage combine >> "$log_file" 2>&1 || true

        # Generate coverage report
        echo "[$package] Coverage Report:" >> "$log_file"
        echo "======================================" >> "$log_file"
        uv run coverage report --show-missing >> "$log_file" 2>&1 || true
    else
        echo "[$package] No coverage data generated" >> "$log_file"
    fi

    echo "[$package] Completed" >> "$log_file"
}

# Export function for parallel execution
export -f run_package_tests
export LOG_DIR

# Array to hold background PIDs
pids=()

# Start all tests in parallel
echo "Starting parallel test execution for ${#packages[@]} packages..."
for pkg_entry in "${packages[@]}"; do
    package="${pkg_entry%%:*}"
    path="${pkg_entry#*:}"
    run_package_tests "$package" "$path" &
    pids+=($!)
    echo "Started $package (PID: $!)"
done

# Wait for all background processes to complete
echo ""
echo "Waiting for all tests to complete..."
for pid in "${pids[@]}"; do
    wait "$pid"
done

echo ""
echo "All tests completed. Results saved to $LOG_DIR/"
echo ""
echo "Summary of log files:"
ls -lh "$LOG_DIR"/*.log

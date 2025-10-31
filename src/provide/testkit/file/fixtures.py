#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""File and Directory Test Fixtures.

Core file testing fixtures with re-exports from specialized modules.
Common fixtures for testing file operations, creating temporary directories,
and standard test file structures used across the provide-io ecosystem."""

from provide.testkit.file.content_fixtures import (
    temp_binary_file,
    temp_csv_file,
    temp_file,
    temp_file_with_content,
    temp_json_file,
    temp_named_file,
)
from provide.testkit.file.directory_fixtures import (
    empty_directory,
    nested_directory_structure,
    temp_directory,
    test_files_structure,
)
from provide.testkit.file.special_fixtures import (
    binary_file,
    readonly_file,
    temp_executable_file,
    temp_symlink,
)

__all__ = [
    "binary_file",
    "empty_directory",
    "nested_directory_structure",
    "readonly_file",
    "temp_binary_file",
    "temp_csv_file",
    "temp_directory",
    "temp_executable_file",
    "temp_file",
    "temp_file_with_content",
    "temp_json_file",
    "temp_named_file",
    "temp_symlink",
    "test_files_structure",
]

# 🧪✅🔚

#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Archive testing fixtures for the provide-io ecosystem.

Standard fixtures for testing archive operations (tar, zip, gzip, bzip2)
across any project that depends on provide.foundation."""

from provide.testkit.archive.fixtures import (
    archive_stress_test_files,
    archive_test_content,
    archive_with_permissions,
    corrupted_archives,
    large_file_for_compression,
    multi_format_archives,
)

__all__ = [
    "archive_stress_test_files",
    "archive_test_content",
    "archive_with_permissions",
    "corrupted_archives",
    "large_file_for_compression",
    "multi_format_archives",
]

# 🧪✅🔚

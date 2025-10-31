#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Script to enforce header and footer conformance on Python files.

This script ensures all Python files have:
- Proper SPDX headers
- Consistent module docstrings
- Repository-specific footer emojis

Usage:
    # Process current directory
    python conform.py --footer "# 🐍🏗️🔚"

    # Process specific directory
    python conform.py --footer "# 🐍🏗️🔚" /path/to/repo

    # Dry run to see what would be processed
    python conform.py --footer "# 🐍🏗️🔚" --dry-run"""

import argparse
import ast
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# --- Protocol Constants ---

HEADER_SHEBANG = "#!/usr/bin/env python3"
HEADER_LIBRARY = "# "
SPDX_BLOCK = [
    "# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.",
    "# SPDX-License-Identifier: Apache-2.0",
    "#",
]
PLACEHOLDER_DOCSTRING = '"""TODO: Add module docstring."""'

# Directories to exclude when scanning
EXCLUDE_DIRS = {
    '.venv', 'venv', 'workenv', '.git', 'build', 'dist', '__pycache__',
    '.pytest_cache', '.ruff_cache', '.mypy_cache', '.hypothesis', '.eggs', '.tox'
}

# --- Logic ---

def find_module_docstring_and_body_start(content: str) -> Tuple[Optional[str], int]:
    """
    Parses the Python source code to find the module-level docstring
    and the line number where the main body of the code starts.

    Returns:
        A tuple containing the docstring string (if found) and the
        1-based line number where the code body begins.
    """
    try:
        tree = ast.parse(content)
        docstring = ast.get_docstring(tree)

        if not tree.body:
            return docstring, len(content.splitlines()) + 1

        first_node = tree.body[0]
        start_lineno = first_node.lineno

        # If the first node is the docstring, the actual code starts after it.
        if isinstance(first_node, ast.Expr) and isinstance(first_node.value, ast.Str):
            if len(tree.body) > 1:
                # The "body" starts at the next node
                start_lineno = tree.body[1].lineno
            else:
                # The file ONLY contains a docstring
                start_lineno = len(content.splitlines()) + 1 # End of file

        return docstring, start_lineno
    except SyntaxError:
        # If the file is not valid Python, we can't parse it.
        # We'll treat it as having no docstring and starting at line 1.
        return None, 1


def conform_file(filepath: str, footer: str) -> None:
    """
    Applies the header and footer protocol to a single Python file.

    Args:
        filepath: Path to the Python file
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            content = "".join(lines)
    except (IOError, UnicodeDecodeError) as e:
        print(f"Error reading file {filepath}: {e}", file=sys.stderr)
        return

    if not lines:
        # Handle empty files
        final_content = "\n".join([HEADER_LIBRARY] + SPDX_BLOCK) + "\n\n" + PLACEHOLDER_DOCSTRING + "\n\n" + footer + "\n"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_content)
        return


    # 1. Determine Header Type
    is_executable = lines[0].strip().startswith("#!")
    header_first_line = HEADER_SHEBANG if is_executable else HEADER_LIBRARY

    # 2. Preserve Docstring and find code body
    docstring, body_start_lineno = find_module_docstring_and_body_start(content)

    if docstring is None:
        docstring_str = PLACEHOLDER_DOCSTRING
    else:
        # Preserve original docstring formatting
        docstring_str = f'"""{docstring}"""'


    # 3. Extract the code body
    # The body is everything from the determined start line to the end,
    # minus any old footers.
    body_lines = lines[body_start_lineno - 1:]
    body_content = "".join(body_lines).rstrip()

    # Strip any old footers - look for emoji patterns that indicate footers
    body_lines_stripped = body_content.splitlines()
    cleaned_body_lines = []
    footer_emojis = ['🏗️', '🐍', '🧱', '🐝', '📁', '🍽️', '📖', '🧪', '✅', '🧩', '🔧', '🌊', '🪢', '🔌', '📞', '📄', '⚙️', '🥣', '🔬', '🔼', '🌶️', '📦', '🧰', '🌍', '🪄', '🔚']
    for line in body_lines_stripped:
        # Skip lines that contain footer emojis
        has_footer_emoji = any(emoji in line for emoji in footer_emojis)
        if not has_footer_emoji:
            cleaned_body_lines.append(line)

    body_content = "\n".join(cleaned_body_lines).rstrip()


    # 4. Construct the new file content
    final_header = "\n".join([header_first_line] + SPDX_BLOCK)

    # Ensure there's content to separate from the footer
    if body_content:
        final_content = f"{final_header}\n\n{docstring_str}\n\n{body_content}\n\n{footer}\n"
    else: # Handles files that might only have a docstring
        final_content = f"{final_header}\n\n{docstring_str}\n\n{footer}\n"


    # 5. Write the conformed content back to the file
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_content)
    except IOError as e:
        print(f"Error writing to file {filepath}: {e}", file=sys.stderr)


def find_python_files(directory: Path) -> list[Path]:
    """
    Recursively find all Python files in a directory, excluding common build/cache directories.

    Args:
        directory: Root directory to search

    Returns:
        List of Python file paths
    """
    python_files = []

    for root, dirs, files in os.walk(directory):
        # Remove excluded directories from the search
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)

    return sorted(python_files)


def main():
    parser = argparse.ArgumentParser(
        description="Enforce header and footer conformance on Python files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--footer",
        required=True,
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to process (default: current directory)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would be processed without making changes"
    )

    args = parser.parse_args()

    directory = Path(args.directory).resolve()

    if not directory.exists():
        print(f"Error: Directory {directory} does not exist", file=sys.stderr)
        sys.exit(1)

    if not directory.is_dir():
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Find all Python files
    python_files = find_python_files(directory)

    if not python_files:
        print(f"No Python files found in {directory}", file=sys.stderr)
        sys.exit(0)

    print(f"Found {len(python_files)} Python files in {directory}")

    if args.dry_run:
        print("\nDry run - files that would be processed:")
        for filepath in python_files:
            print(f"  {filepath}")
        sys.exit(0)

    # Process each file
    for filepath in python_files:
        conform_file(str(filepath), args.footer)



if __name__ == "__main__":
    main()

# 🧪✅🔚

#!/usr/bin/env python3
# _install_pth.py
#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Post-install script to symlink .pth file to site-packages root.

This script is called automatically via pip's console_scripts entry point
after package installation to ensure the .pth file is in the correct location.
"""

from __future__ import annotations

import os
import site
import sys
from pathlib import Path


def install_pth_file(*, verbose: bool = False) -> int:
    """Install/symlink .pth file to site-packages root.

    Returns:
        0 on success, 1 on failure
    """
    # Find site-packages directory
    site_packages = None
    if hasattr(site, "getsitepackages"):
        site_dirs = site.getsitepackages()
        if site_dirs:
            site_packages = Path(site_dirs[0])

    if not site_packages:
        # Fallback
        if sys.platform == "win32":
            site_packages = Path(sys.prefix) / "Lib" / "site-packages"
        else:
            python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
            site_packages = Path(sys.prefix) / "lib" / python_version / "site-packages"

    # Source .pth file (in package)
    pth_source = Path(__file__).parent / "provide_testkit_init.pth"

    # Destination .pth file (in site-packages root)
    pth_dest = site_packages / "provide_testkit_init.pth"

    if not pth_source.exists():
        print(f"Error: Source .pth file not found at {pth_source}", file=sys.stderr)
        return 1

    try:
        # Always copy (not symlink) so it survives package uninstall
        # A symlink would break when the package is removed, leaving a dangling
        # .pth file that errors on Python startup
        import shutil

        if pth_dest.exists() or pth_dest.is_symlink():
            pth_dest.unlink()

        shutil.copy2(pth_source, pth_dest)
        if verbose:
            print(f"✓ Installed {pth_dest}")
        return 0

    except PermissionError:
        if verbose:
            print(f"Warning: No permission to write to {pth_dest}", file=sys.stderr)
            print("The setproctitle blocker will use fallback mechanisms", file=sys.stderr)
        return 0  # Don't fail installation
    except Exception as e:
        if verbose:
            print(f"Warning: Could not install .pth file: {e}", file=sys.stderr)
            print("The setproctitle blocker will use fallback mechanisms", file=sys.stderr)
        return 0  # Don't fail installation


def uninstall_pth_file() -> int:
    """Remove .pth file from site-packages root.

    This should be called when the package is uninstalled to clean up
    the .pth file that was installed to site-packages root.

    Returns:
        0 on success, 1 on failure
    """
    # Find site-packages directory
    site_packages = None
    if hasattr(site, "getsitepackages"):
        site_dirs = site.getsitepackages()
        if site_dirs:
            site_packages = Path(site_dirs[0])

    if not site_packages:
        # Fallback
        if sys.platform == "win32":
            site_packages = Path(sys.prefix) / "Lib" / "site-packages"
        else:
            python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
            site_packages = Path(sys.prefix) / "lib" / python_version / "site-packages"

    # .pth file location
    pth_dest = site_packages / "provide_testkit_init.pth"

    try:
        if pth_dest.exists() or pth_dest.is_symlink():
            pth_dest.unlink()
            print(f"✓ Removed {pth_dest}")
            return 0
        else:
            print(f"ℹ  .pth file not found at {pth_dest}")
            return 0
    except PermissionError:
        print(f"Warning: No permission to remove {pth_dest}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error removing .pth file: {e}", file=sys.stderr)
        return 1


def _cli_install() -> int:
    """CLI entry point for install command."""
    return install_pth_file(verbose=True)


def _cli_uninstall() -> int:
    """CLI entry point for uninstall command."""
    return uninstall_pth_file()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        sys.exit(_cli_uninstall())
    else:
        sys.exit(_cli_install())


# 📦🔗⚙️✨

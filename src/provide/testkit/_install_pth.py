#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Post-install script to symlink .pth file to site-packages root.

This script is called automatically via the console_scripts entry point
after package installation to ensure the .pth file is in the correct location."""

from __future__ import annotations

from pathlib import Path
import site
import sys

from provide.foundation.console.output import perr, pout


def _resolve_site_packages() -> Path:
    """Return the best-guess site-packages directory."""
    site_packages: Path | None = None
    if hasattr(site, "getsitepackages"):
        site_dirs = site.getsitepackages()
        if site_dirs:
            site_packages = Path(site_dirs[0])

    if site_packages is not None:
        return site_packages

    if sys.platform == "win32":
        return Path(sys.prefix) / "Lib" / "site-packages"

    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    return Path(sys.prefix) / "lib" / python_version / "site-packages"


def install_pth_file(*, verbose: bool = False) -> int:
    """Install/symlink .pth file to site-packages root.

    Returns:
        0 on success, 1 on failure
    """
    site_packages = _resolve_site_packages()

    # Source .pth file (in package)
    pth_source = Path(__file__).parent / "provide_testkit_init.pth"

    # Destination .pth file (in site-packages root)
    pth_dest = site_packages / "provide_testkit_init.pth"

    if not pth_source.exists():
        perr(f"Error: Source .pth file not found at {pth_source}")
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
            pout(f"✓ Installed {pth_dest}")
        return 0

    except PermissionError:
        if verbose:
            perr(f"Warning: No permission to write to {pth_dest}")
            perr("The setproctitle blocker will use fallback mechanisms")
        return 0  # Don't fail installation
    except Exception as e:
        if verbose:
            perr(f"Warning: Could not install .pth file: {e}")
            perr("The setproctitle blocker will use fallback mechanisms")
        return 0  # Don't fail installation


def uninstall_pth_file() -> int:
    """Remove .pth file from site-packages root.

    This should be called when the package is uninstalled to clean up
    the .pth file that was installed to site-packages root.

    Returns:
        0 on success, 1 on failure
    """
    site_packages = _resolve_site_packages()

    # .pth file location
    pth_dest = site_packages / "provide_testkit_init.pth"

    try:
        if pth_dest.exists() or pth_dest.is_symlink():
            pth_dest.unlink()
            pout(f"✓ Removed {pth_dest}")
            return 0
        else:
            pout(f"i  .pth file not found at {pth_dest}")
            return 0
    except PermissionError:
        perr(f"Warning: No permission to remove {pth_dest}")
        return 1
    except Exception as e:
        perr(f"Error removing .pth file: {e}")
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

# 🧪✅🔚

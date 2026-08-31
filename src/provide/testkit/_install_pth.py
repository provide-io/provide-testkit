#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Post-install script to symlink .pth file to site-packages root.

This script is called automatically via the console_scripts entry point
after package installation to ensure the .pth file is in the correct location."""

from __future__ import annotations

from pathlib import Path
import sys

from provide.foundation.console.output import perr, pout

_SITE_PACKAGES_NAMES = frozenset({"site-packages", "dist-packages"})


def _prefix_site_packages() -> Path:
    """Return the site-packages directory implied by ``sys.prefix``."""
    if sys.platform == "win32":
        return Path(sys.prefix) / "Lib" / "site-packages"

    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    return Path(sys.prefix) / "lib" / python_version / "site-packages"


def _resolve_site_packages() -> Path:
    """Return the site-packages directory this package is installed into.

    ``site.getsitepackages()`` is deliberately not used. ``install_pth_file`` runs
    during Python's site initialization, because the .pth file imports this
    package -- and .pth files are processed from inside ``site.venv()``, which
    reads them *before* it rewrites ``site.PREFIXES`` for the virtual
    environment. A call made at that moment reports the base interpreter's
    directories, not the venv's, so the .pth was written into the shared
    interpreter: inert there, invisible to the venv, and beyond the reach of a
    later upgrade, which is why a stale .pth could never be refreshed.

    The directory holding ``provide/testkit/`` is the right answer by
    construction and needs no interpreter state at all. ``sys.prefix`` is the
    fallback -- unlike ``site.PREFIXES`` it already points at the venv this
    early -- and covers an editable install, where this file lives in a source
    tree that site.py would never read a .pth from.
    """
    package_parent = Path(__file__).resolve().parents[2]
    if package_parent.name in _SITE_PACKAGES_NAMES:
        return package_parent

    return _prefix_site_packages()


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

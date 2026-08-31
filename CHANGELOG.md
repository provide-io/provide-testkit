# Changelog

All notable changes to the provide-testkit project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.5] - 2026-08-30

### Fixed
- **The `.pth` file was installed into the base interpreter instead of the
  virtual environment.** `install_pth_file()` asked `site.getsitepackages()`
  where to write. It runs during Python's site initialization — the .pth file
  imports this package — and .pth files are processed from inside `site.venv()`,
  which reads them *before* it rewrites `site.PREFIXES` for the virtual
  environment. Captured at the moment of the copy:

  ```
  sys.prefix    = <venv>                                  # correct
  site.PREFIXES = ['/…/uv/python/cpython-3.11.16-…']       # base interpreter
  dst           = <base>/lib/python3.11/site-packages/provide_testkit_init.pth
  ```

  Two consequences. The file landed in the shared interpreter, where no
  `provide` package exists, so it did nothing but persist — surviving
  uninstallation from every project. And because the copy never reached the
  venv, a `.pth` already there was never refreshed: upgrading the package left
  the old file in place, which is what kept 0.4.4's fix from reaching existing
  environments.

  The destination is now the directory that contains `provide/testkit/`, which
  is correct by construction and reads no interpreter state. `sys.prefix` is the
  fallback for an editable install; unlike `site.PREFIXES` it already points at
  the venv this early.

  Verified: planting a stale `.pth` in a 0.4.5 environment and running Python
  once replaces it and fixes the C locale, and the base interpreter is never
  written to.

  If an earlier version left a `provide_testkit_init.pth` in your base
  interpreter's `site-packages`, it is inert and safe to delete; `uninstall`
  targets the environment it runs in and will not find it.

## [0.4.4] - 2026-08-30

### Fixed
- **The `.pth` file is ASCII again, so Python starts under the C locale.**
  `provide_testkit_init.pth` carried a literal emoji in its two `TESTKIT_PTH_LOG`
  debug messages. `site.py` on Python 3.11 and 3.12 reads `.pth` files with the
  locale's encoding, which is ASCII under the C locale, so those bytes aborted
  interpreter startup for every program in the environment — before any user code
  ran:

  ```
  Fatal Python error: init_import_site: Failed to import the site module
  UnicodeDecodeError: 'ascii' codec can't decode byte 0xf0 in position 67
  ```

  `python -c "print('hello')"` failed the same way in any environment with
  testkit installed; it was not specific to running tests. Python 3.13 reads
  `.pth` files as UTF-8 and was never affected, which is why the repository's own
  environment never showed it.

  The emoji is kept, written as a `\U0001F50C` escape that the line's own Python
  parsing resolves, so the debug output is unchanged while the file itself is
  ASCII. Two tests hold it there: one rejects any byte above `0x7F`, the other
  resolves the escapes and requires the emoji to still be present, so satisfying
  the first by deleting the emoji fails the second.

### Removed
- **The `fuzzing` extra**, and its entry in `all`. It could not be installed on
  any modern Python: pynguin >= 0.46 requires `pytest>=8.3.5,<9.0.0`, which this
  project's own `pytest>=9.0.2` rules out, and the only pynguin loose enough to
  coexist with pytest 9 is 0.6.3 (2021), which depends on a jellyfish release
  with no cp313 wheels and an sdist `uv` refuses to parse. `uv sync --all-extras`
  failed outright because of it. The reasoning is recorded in `pyproject.toml` so
  the extra can be restored when pynguin supports pytest 9.

### Changed
- Dependencies upgraded to their latest releases. Three mypy strict errors
  surfaced from newer stubs and are fixed: PyYAML now ships types, making two
  `type: ignore[import-untyped]` comments dead, and memray now resolves as a
  module, so its optional-import sentinel needed the assignment suppressed.
- The release pipeline was repaired and hardened: publishing jobs are gated on
  the release event, the SBOM runs in its own job away from the signing key and
  describes this package rather than the tool that generated it, extras are
  chosen by dependence, and a repair path exists for a release that lost its
  artifacts.
- Quality reports this package generates are no longer tracked in git.

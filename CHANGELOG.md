# Changelog

All notable changes to the provide-testkit project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

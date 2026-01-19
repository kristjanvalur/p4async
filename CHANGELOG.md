# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Updated README to reflect that the GIL/blocking connect() issue was fixed in p4python 2025.2
  - Changed prominent "Caveats" section to a footnote-style note
  - Users are now advised to use p4python 2025.2 or later for optimal async performance

## [0.1.6] - 2025-10-02

### Added
- Comprehensive wrapping tests to verify async delegation patterns
  - Added `test_p4async_wrapping.py` with 24 tests covering all async wrapping patterns
  - Tests verify call chains: async methods → execute() → sync methods
  - Tests verify `simple_wrap_methods` pattern (connect, disconnect, run_tickets)
  - Tests verify `run_wrap_methods` pattern (run_login, run_submit, etc.)
  - Tests verify `arun()` and `run(with_async=True)` delegation through sync_run()
  - Tests verify thread pool execution and lock acquisition
- Enhanced `fake_p4.py` with implementations for run_wrap_methods
  - Added run_submit, run_shelve, delete_shelve implementations
  - Added run_login, run_password implementations
  - Added run_filelog, run_print, run_resolve implementations

### Fixed
- Fixed lookup order in `__getattr__` to catch `run_*` method specializations before falling back to generic `arun_*` pattern
  - This ensures methods like `run_login` are properly recognized and wrapped

## [0.1.5] - 2025-09-25

### Added
- Added Copilot instructions file for AI-assisted development
- Added CI/CD workflow for automated testing and releases

### Changed
- Removed old README file in favor of current README.md
- Updated GitHub Actions workflow configuration

### Fixed
- Fixed simple wrap methods to run inside lock for proper thread safety
  - Methods like `connect()`, `disconnect()`, and `run_tickets()` now properly acquire lock

## [0.1.4] - 2025-08-21

### Changed
- Moved thread lock from P4Async initialization into the `sync_run()` method
  - Improves thread safety by ensuring lock is held during actual P4 operations

### Added
- Additional unit tests for concurrent operations
- Fake P4 implementation for testing without real Perforce server
  - Supports canned responses for testing
  - Simulates concurrent request limitations
  - Supports deterministic concurrency testing with block events

## [0.1.3] - 2025-08-20

Initial tagged release with basic async wrapper functionality.

### Added
- Core `P4Async` class extending `P4.P4` with async support
- Dynamic async method generation via `__getattr__`
- Thread-safe execution with per-connection locks
- Two wrapping patterns:
  - `simple_wrap_methods`: Direct thread execution for connect/disconnect
  - `run_wrap_methods`: Delegate to run() with `with_async=True`
- Support for `run(with_async=True)` to return awaitable
- Async context manager support (`async with P4Async()`)
- Basic test suite

[Unreleased]: https://github.com/kristjanvalur/p4async/compare/v0.1.6...HEAD
[0.1.6]: https://github.com/kristjanvalur/p4async/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/kristjanvalur/p4async/compare/v.0.1.4...v0.1.5
[0.1.4]: https://github.com/kristjanvalur/p4async/compare/v0.1.3...v.0.1.4
[0.1.3]: https://github.com/kristjanvalur/p4async/releases/tag/v0.1.3

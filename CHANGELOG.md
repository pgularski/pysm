# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.4.1] - 2026-06-17

### Fixed

- Fixed MicroPython compatibility for optional queued, async queued, and serialization modules by reusing the core deque compatibility wrapper.
- Replaced async callback awaitable detection's dependency on `inspect.isawaitable` with a lightweight runtime-compatible helper.

### Tests

- Added optional-module regression coverage for MicroPython-style deque construction and awaitable detection.

### CI

- Made patch-release automation generate a versioned changelog entry from merged pull request metadata when an automatic patch bump has no existing release notes.

## [0.4.0] - 2026-06-16

### Added

- Added opt-in queued, thread-safe queued, and async queued runtimes with run-to-completion semantics.
- Added serialization helpers for capturing and restoring state machine snapshots.
- Added a fluent builder API for constructing state machines.
- Added type stubs and `py.typed` packaging metadata.
- Added `initialize(fire_events_on_init=False)` support for firing initial enter handlers without changing the default behavior.

### Changed

- Modernized the package while keeping the classic core import small and dependency-free.
- Refreshed documentation for core usage, optional modules, serialization, and MicroPython boundaries.

### Fixed

- Replaced dispatch-before-initialize assertions with clear `StateMachineException` errors.
- Fixed MicroPython compatibility around unbounded deques, missing `logging`, and missing `collections.defaultdict`.

### CI

- Added GitHub Actions CI, package checks, a MicroPython Unix smoke job, and automatic patch-version bumping after merged package changes.

# AI Coding Assistant Instructions for p4async

## Project Overview
This is an async wrapper around Perforce's `p4python` library. The core class `P4Async` extends `P4.P4` to provide async versions of Perforce commands while maintaining thread safety through per-connection locks.

## Architecture & Key Patterns

### Core Design: Thread-Safe Async Wrapper
- **Single Connection Rule**: Each `P4Async` instance uses a `threading.Lock` to ensure only one operation executes at a time on the underlying P4 connection
- **Dynamic Method Generation**: Methods prefixed with `a` (e.g., `arun`, `aconnect`, `arun_clients`) are auto-generated via `__getattr__` 
- **Two Wrapping Strategies**:
  - `simple_wrap_methods`: Direct thread execution for methods like `connect`, `disconnect`
  - `run_wrap_methods`: Add `with_async=True` to delegate to existing `run()` method

### Method Naming Conventions
```python
# Auto-generated patterns in __getattr__:
p4.arun_clients()     # -> self.arun("clients", ...)
p4.adelete_shelve()   # -> self.arun("shelve", "-d", ...)  
p4.afetch_change()    # -> self.__afetch("change", ...)
p4.asave_change()     # -> self.__asave("change", ...)
```

## Development Workflow

### Environment Setup
- **Package Manager**: Uses `uv` for dependency management and virtual environments
- **Setup**: `uv sync --locked --all-extras --dev` (installs dev dependencies including pytest, pytest-asyncio)
- **Python Version**: Requires Python 3.11+

### Testing Strategy
- **Fake P4 Module**: Tests use `tests/fake_p4.py` which provides a mock `P4` class with response registration
- **Test Setup Pattern**: `conftest.py` uses monkeypatching to replace `P4` module with fake implementation before importing p4async
- **Concurrency Testing**: Key pattern in `test_p4async_concurrent.py` uses `threading.Event` and `block_command`/`block_event` to test deterministic concurrent behavior

### Testing Example
```python
# In tests: register canned responses
p4.register_response("clients", [{"client": "test-client"}])
# Test both sync and async patterns
result = await p4.arun("clients")  # async
result = p4.run("clients", with_async=True)  # returns awaitable
```

### CI/CD Commands
- **Local Testing**: `uv run pytest -q`
- **Linting**: `uvx ruff check` and `uvx ruff format --check`
- **Build**: `uv build`
- **Release**: Uses tag-based releases (`v*` for PyPI, `t*` for TestPyPI)

## Critical Implementation Details

### Thread Safety Requirements
- All P4 operations must acquire `self.lock` before execution (see `sync_run()` and `wrap_lock()`)
- The underlying p4python library is not thread-safe and doesn't release GIL during `connect()`

### Async Context Manager
- Implements `__aenter__`/`__aexit__` for `async with` usage
- Auto-disconnects on context exit if connected

### Key Files to Understand
- `src/p4async/__init__.py`: Core implementation with dynamic method generation
- `tests/fake_p4.py`: Mock P4 implementation crucial for testing patterns
- `tests/conftest.py`: Monkeypatching setup that enables testable isolation
- `pyproject.toml`: uv-based project configuration with dev dependencies

## Common Gotchas
- P4 connection state is per-instance, so concurrent operations need separate instances
- The `with_async=True` parameter transforms sync methods into awaitables
- Test isolation requires careful monkeypatching of the P4 module before import
- Canned responses in tests can be static values or callables accepting `(cmd, *args)`
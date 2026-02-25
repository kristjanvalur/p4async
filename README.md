
# p4async

An async extension to p4python ([PyPI](https://pypi.org/project/p4python/), [GitHub](https://github.com/perforce/p4python)), the Python client for the Perforce (P4) version control server.
This package adds awaitable wrappers around p4python operations for asyncio-based applications.

## Setup

Use your favorite package manager to install the module into your project

- `pip install p4async`
- `uv add p4async`

## Usage

```python
from p4async import P4Async
p4a = P4Async()
await p4a.aconnect()
```

All relevant Perforce commands have async counterparts prefixed with `a`.
For example: `aconnect()`, `arun()`, `arun_clients()`, `afetch_change()`, etc.

Commands are executed with a lock on a worker thread. The way this is done can be
customized via subclassing.

> **Note:** Earlier versions of p4python (prior to 2025.2) did not release the Python GIL (global interpreter lock) during `connect()` calls, which made `aconnect()` blocking. This was fixed in p4python 2025.2. For optimal async performance, use p4python 2025.2 or later.

## Subclassing

`P4Async` provides core async wrappers, while keeping a few hooks intentionally overridable
for custom behavior.

- Override `execute(self, func, *args, **kwargs)` to customize how synchronous work is
	scheduled (for example, custom executors or instrumentation).
- Override `sync_run(self, *args, **kwargs)` to wrap the underlying synchronous `run()` call
	with extra behavior. This is the primary hook around command execution.
- Extend `simple_wrap_methods` and `run_wrap_methods` in a subclass to add additional
	auto-generated async wrappers in the `a<method>` pattern.

```python
from p4async import P4Async


class MyP4Async(P4Async):
    async def execute(self, func, *args, **kwargs):
        # Custom scheduling/telemetry hook
        return await super().execute(func, *args, **kwargs)

    def sync_run(self, *args, **kwargs):
        # Custom behavior around the underlying P4 run()
        return super().sync_run(*args, **kwargs)

    # Example: add async wrappers for extra methods
    simple_wrap_methods = P4Async.simple_wrap_methods | {"my_custom_sync_method"}
```

## Development

- Use [uv](https://docs.astral.sh/uv/) for dependency management and virtual environments.
- Format and lint with ruff:
    - `uvx ruff check`
    - `uvx ruff format --check`
    - `uvx ruff format`
- Run type checking for the package:
    - `uv run mypy src`

## License

MIT

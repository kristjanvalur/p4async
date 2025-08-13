
# p4async

An extension to the p4python module, adding async functionality to Perforce.

## Setup

1. Install [uv](https://github.com/astral-sh/uv) if you don't have it:
   ```powershell
   pip install uv
   ```
2. Install dependencies:
   ```powershell
   uv sync
   ```

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

## Development

- Use `uv` for dependency management and virtual environments.

## License

MIT

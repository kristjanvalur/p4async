
# p4async

An extension to the [p4python](https://pypi.org/project/p4python/) module, adding async functionality to Perforce.

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

## Caveats

It would appear that current versions of p4python do not release
the pythong GIL (global interpreter lock) while doing a `connect()` call. This means that even `aconnect()` is currently blocking.  This might get fixed by Perforce at some point.

## Development

- Use [uv](https://docs.astral.sh/uv/) for dependency management and virtual environments.

## License

MIT

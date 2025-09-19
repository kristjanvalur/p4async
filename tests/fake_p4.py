"""
A fake P4 module to use in tests.

Provides a `P4` class that mimics the real `P4.P4` interface minimally:
- run(cmd, *args) -> delegates to fake_run
- fake_run(cmd, *args) -> returns canned responses or raises for unknown commands
- register_response(cmd, response) -> register a value or callable to produce responses
- __getattr__ to allow attribute-style access on the P4 object

Usage in tests:
    from tests import fake_p4
    fake = fake_p4.P4()
    fake.register_response('login', lambda *a: {'status': 'ok'})
    monkeypatch.setattr('P4', fake_p4)  # or patch where your code imports P4

The module exposes module-level attribute `P4` so code that does `from P4 import P4` can be patched to use this.
"""

import random
import threading
import time
from typing import Any, Callable, Dict


class P4:
    """Minimal fake of P4.P4.

    Instances hold a registry of canned responses for commands. Responses can be:
    - a static value (returned as-is)
    - a callable taking (cmd, *args) returning a value

    The real P4.run usually returns a Python list/dict structure; tests can register similar types.
    """

    def __init__(self) -> None:
        self._responses: Dict[str, Callable[..., Any]] = {}
        # common attributes to mimic the real P4 object
        self.connected = False
        self.user = None
        self.client = None
        # A lock to simulate that the real P4 connection only allows one concurrent request
        self._request_lock = threading.Lock()
        # Optional event and command name to support deterministic blocking in tests.
        # If `block_event` is set and `block_command` matches the command being run,
        # fake_run will wait on the event while holding the request lock.
        self.block_event = None
        self.block_command = None

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def register_response(self, cmd: str, response: Any) -> None:
        """Register a canned response for a command.

        Args:
            cmd: command name string, e.g. 'login', 'fstat', 'changes'
            response: either a static value or a callable (cmd, *args) -> value
        """
        if callable(response):
            self._responses[cmd] = response  # type: ignore[assignment]
        else:
            # wrap static values in a callable for uniformity
            self._responses[cmd] = lambda _cmd, *a, _r=response: _r

    def run(self, cmd: str, *args: Any) -> Any:
        """Public run method that mirrors P4.run(cmd, ...) signature.

        Returns whatever fake_run returns or raises a RuntimeError for unknown commands.
        """
        return self.fake_run(cmd, *args)

    def fake_run(self, cmd: str, *args: Any) -> Any:
        """Execute a canned response for cmd.

        If no canned response is found, raises RuntimeError to indicate missing stub.
        """
        # Try to acquire the request lock without blocking. If it's already held by
        # another thread, return a Perforce-style error response indicating only one
        # concurrent request is allowed on a connection.
        acquired = self._request_lock.acquire(blocking=False)
        if not acquired:
            # Return an error-like response (lists/dicts are common with p4python)
            return [
                {"code": "error", "data": "Only one concurrent request can be made on a connection"}
            ]

        try:
            # If tests set a block_event and the command matches, wait on the event
            # while holding the lock to simulate a long-running request.
            if self.block_event is not None and self.block_command == cmd:
                self.block_event.wait()

            # Simulate a small variable processing delay (0-10ms) while holding the lock
            time.sleep(random.random() * 0.01)

            if cmd in self._responses:
                try:
                    return self._responses[cmd](cmd, *args)
                except TypeError:
                    # In case the registered callable doesn't accept (cmd, *args), try calling without cmd
                    return self._responses[cmd](*args)
            # Some tests might expect commands to be unknown and return empty list
            raise RuntimeError(f"No fake response registered for command: {cmd}")
        finally:
            self._request_lock.release()

    def __getattr__(self, name: str) -> Any:
        """Allow attribute access for commonly accessed attributes.

        For unknown attributes, raise AttributeError to mimic normal behavior.
        """
        if name in ("connected", "user", "client"):
            return object.__getattribute__(self, name)

        # Provide a callable that forwards to run for common P4 command methods
        def _cmd_method(*args: Any):
            return self.run(name, *args)

        return _cmd_method


# Expose module-level P4 so tests can monkeypatch `P4` module imports.
# Tests that do `import P4` or `from P4 import P4` can be monkeypatched to use this module.


# Provide a convenience factory at module level for easier monkeypatching
def P4Factory() -> P4:
    return P4()

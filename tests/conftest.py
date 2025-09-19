import importlib
import sys
from pathlib import Path

import pytest


@pytest.fixture()
def p4async_module(monkeypatch):
    """Monkeypatch the imported `P4` module before importing `p4async`.

    This ensures `p4async` will build `P4Async` on top of our fake P4 implementation.
    """
    # import the fake p4 module
    import tests.fake_p4 as fake_p4

    # Insert fake module into sys.modules as 'P4' so `import P4` in p4async resolves to it
    monkeypatch.setitem(sys.modules, "P4", fake_p4)

    # Ensure the project's src/ directory is on sys.path so importlib can find p4async
    repo_root = Path(__file__).resolve().parents[1]
    src_path = str(repo_root / "src")
    monkeypatch.syspath_prepend(src_path)

    # Ensure p4async is (re)imported so it picks up our fake module
    if "p4async" in sys.modules:
        del sys.modules["p4async"]

    p4async = importlib.import_module("p4async")
    return p4async

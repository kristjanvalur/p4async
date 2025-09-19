import pytest

import tests.fake_p4 as fake_p4


def test_connect_and_disconnect():
    p4 = fake_p4.P4()
    assert not p4.connected
    p4.connect()
    assert p4.connected
    p4.disconnect()
    assert not p4.connected


def test_clients_list_like_p4python():
    p4 = fake_p4.P4()
    # Example p4.run('clients') returns a list of dicts with client names
    p4.register_response("clients", [{"client": "dev1"}, {"client": "dev2"}])

    out = p4.run("clients")
    assert isinstance(out, list)
    assert out[0]["client"] == "dev1"

    # attribute-style
    out2 = p4.clients()
    assert out2 == out


def test_info_and_login():
    p4 = fake_p4.P4()

    # p4.run('login') commonly returns a list or a confirmation string
    p4.register_response("login", ["User test logged in"])
    assert p4.run("login") == ["User test logged in"]

    # p4.run('info') typically returns a dict with user/client
    p4.register_response("info", lambda cmd, *a: {"user": "tester", "client": "main"})
    info = p4.info()
    assert info["user"] == "tester"
    assert info["client"] == "main"


def test_fstat_and_changes_like_examples():
    p4 = fake_p4.P4()

    # fstat returns metadata for files
    p4.register_response(
        "fstat", lambda cmd, *a: [{"depotFile": "//depot/file.txt", "action": "edit"}]
    )
    res = p4.run("fstat", "//depot/file.txt")
    assert isinstance(res, list)
    assert res[0]["depotFile"].endswith("file.txt")

    # changes returns a list of changelists
    p4.register_response(
        "changes", lambda cmd, *a: [{"change": 101, "desc": "fix"}, {"change": 100, "desc": "init"}]
    )
    changes = p4.changes("-m", "2")
    assert isinstance(changes, list)
    assert changes[0]["change"] == 101


def test_error_like_when_not_registered():
    p4 = fake_p4.P4()
    with pytest.raises(RuntimeError):
        p4.run("some_unknown_command")

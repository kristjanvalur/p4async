import pytest

import tests.fake_p4 as P4


def test_run_clients_via_run():
    p4 = P4.P4()
    p4.register_response("clients", [{"client": "alpha"}, {"client": "beta"}])

    res = p4.run("clients")
    assert isinstance(res, list)
    assert res[0]["client"] == "alpha"
    assert res[1]["client"] == "beta"


def test_run_clients_via_method():
    p4 = P4.P4()
    p4.register_response("clients", lambda cmd, *a: [{"client": "one"}])

    res = p4.clients()
    assert res == [{"client": "one"}]


def test_login_and_info():
    p4 = P4.P4()

    # static response for login
    p4.register_response("login", ["User logged in"])

    # dynamic response for info
    def info_resp(cmd, *args):
        return {"user": "tester", "client": "test-client"}

    p4.register_response("info", info_resp)

    assert p4.run("login") == ["User logged in"]
    info = p4.info()
    assert info["user"] == "tester"
    assert info["client"] == "test-client"


def test_unknown_command_raises():
    p4 = P4.P4()
    with pytest.raises(RuntimeError):
        p4.run("nonexistent")


def test_dynamic_args_in_response():
    p4 = P4.P4()

    def changes_resp(cmd, *args):
        # echo back args for testing
        return {"cmd": cmd, "args": args}

    p4.register_response("changes", changes_resp)

    out = p4.run("changes", "-m", "5")
    assert out["cmd"] == "changes"
    assert out["args"] == ("-m", "5")

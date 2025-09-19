import pytest


@pytest.mark.asyncio
async def test_arun_clients(p4async_module):
    p4async = p4async_module
    p4 = p4async.P4Async()

    # Register a fake clients response
    p4.register_response("clients", [{"client": "async-client"}])

    # Use arun to run asynchronously
    out = await p4.arun("clients")
    assert isinstance(out, list)
    assert out[0]["client"] == "async-client"


@pytest.mark.asyncio
async def test_arun_info_and_run_with_async_flag(p4async_module):
    p4async = p4async_module
    p4 = p4async.P4Async()

    # register info and changes responses
    p4.register_response("info", lambda cmd, *a: {"user": "async-user", "client": "async-client"})
    p4.register_response("changes", lambda cmd, *a: [{"change": 1}])

    # attribute-style arun (p4.arun_info())
    info = await p4.arun_info()
    assert info["user"] == "async-user"

    # run with with_async=True should return an awaitable
    aw = p4.run("changes", with_async=True)
    assert hasattr(aw, "__await__")
    changes = await aw
    assert changes[0]["change"] == 1


@pytest.mark.asyncio
async def test_execute_and_sync_run(p4async_module):
    p4async = p4async_module
    p4 = p4async.P4Async()

    # register fstat to return immediate sync result
    p4.register_response("fstat", lambda cmd, *a: [{"depotFile": "//depot/file.txt"}])

    # sync_run should return immediately (not a coroutine)
    res = p4.sync_run("fstat", "//depot/file.txt")
    assert isinstance(res, list)
    assert res[0]["depotFile"].endswith("file.txt")

    # the async wrapper execute should run sync_run in executor and return same result
    res2 = await p4.execute(p4.sync_run, "fstat", "//depot/file.txt")
    assert res2 == res

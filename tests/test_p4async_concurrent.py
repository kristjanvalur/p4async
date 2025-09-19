import asyncio
import threading
import time

import pytest


@pytest.mark.asyncio
async def test_two_instances_arun_concurrent(p4async_module):
    """Verify two P4Async instances execute underlying requests concurrently (on different threads).

    Use a threading.Event to block both underlying requests while they hold their per-connection
    request locks. Assert both locks are held before releasing the event so we deterministically
    exercise concurrency.
    """
    # Use the shared fixture which already monkeypatches P4 and imports p4async
    p4async = p4async_module

    # Create a shared event that will block the underlying fake_run when called with 'longop'
    evt = threading.Event()

    a = p4async.P4Async()
    b = p4async.P4Async()

    a.register_response("longop", lambda cmd, *a: ["done-a"])
    b.register_response("longop", lambda cmd, *a: ["done-b"])

    # Configure both instances to block on the same command and event
    a.block_event = evt
    a.block_command = "longop"
    b.block_event = evt
    b.block_command = "longop"

    # Start both arun tasks concurrently
    t1 = asyncio.create_task(a.arun("longop"))
    t2 = asyncio.create_task(b.arun("longop"))

    # Wait until both underlying request locks are held (i.e., both threads reached blocking wait)
    deadline = time.time() + 2.0
    while True:
        if a._request_lock.locked() and b._request_lock.locked():
            break
        if time.time() > deadline:
            raise AssertionError("Timed out waiting for both request locks to be acquired")
        await asyncio.sleep(0.001)

    # At this point both underlying requests should be blocking and holding their respective locks.
    assert a._request_lock.locked()
    assert b._request_lock.locked()

    # Release the event so both threads proceed and complete
    evt.set()

    r1 = await t1
    r2 = await t2

    assert r1 == ["done-a"]
    assert r2 == ["done-b"]

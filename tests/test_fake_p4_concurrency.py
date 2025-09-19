import threading
import time

import tests.fake_p4 as fake_p4


def test_concurrent_request_returns_error():
    p4 = fake_p4.P4()

    # Set up a blocking event so the first call will block while holding the request lock.
    evt = threading.Event()
    p4.block_event = evt
    p4.block_command = "longop"

    # Register a response for the long operation so the blocked thread will get a result after event is set.
    p4.register_response("longop", lambda cmd, *a: ["done"])

    results = []

    def worker():
        results.append(p4.run("longop"))

    t = threading.Thread(target=worker)
    t.start()

    # Wait until the background thread has acquired the request lock and is blocking.
    # Poll the internal lock to ensure deterministic behavior.
    timeout = time.time() + 1.0
    while not p4._request_lock.locked():
        if time.time() > timeout:
            raise RuntimeError("Background thread did not acquire lock in time")
        time.sleep(0.001)

    # Now perform a concurrent call on the main thread; it should immediately return the error response.
    out = p4.run("longop")
    assert isinstance(out, list)
    assert out and out[0].get("code") == "error"

    # Release the event to allow the background thread to finish and join it.
    evt.set()
    t.join()

    # Background thread should have completed with the successful response.
    assert results == [["done"]]

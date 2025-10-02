"""
Tests that verify the wrapping and delegation patterns for async methods.

These tests verify that async methods (like aconnect(), arun(), arun_login())
properly delegate through the execute(), wrap_lock(), and sync_run() chain to
reach the underlying synchronous methods.
"""

import asyncio
import sys
from unittest.mock import AsyncMock, Mock, call, patch

import pytest

# Import p4async to get method names for parametrization
# This will be monkeypatched in the fixture, but we need it for test collection
if "p4async" not in sys.modules:
    # During test collection, import from source to get the method sets
    sys.path.insert(0, str(__file__).rsplit("tests", 1)[0] + "src")
    try:
        import p4async as _p4async_source

        SIMPLE_WRAP_METHODS = list(_p4async_source.P4Async.simple_wrap_methods)
        RUN_WRAP_METHODS = list(_p4async_source.P4Async.run_wrap_methods)
    except ImportError:
        # Fallback if import fails
        SIMPLE_WRAP_METHODS = ["connect", "disconnect", "run_tickets"]
        RUN_WRAP_METHODS = [
            "run_submit",
            "run_shelve",
            "delete_shelve",
            "run_login",
            "run_password",
            "run_filelog",
            "run_print",
            "run_resolve",
        ]
else:
    SIMPLE_WRAP_METHODS = list(sys.modules["p4async"].P4Async.simple_wrap_methods)
    RUN_WRAP_METHODS = list(sys.modules["p4async"].P4Async.run_wrap_methods)


class TestSimpleWrapMethods:
    """Test that simple_wrap_methods follow the correct async execution pattern"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method_name", SIMPLE_WRAP_METHODS)
    async def test_async_method_calls_through_execute_and_wrap_lock(
        self, p4async_module, method_name
    ):
        """Verify that async wrapper -> execute() -> wrap_lock(method) -> method()"""
        p4async = p4async_module
        p4 = p4async.P4Async()

        # Special setup for disconnect (needs to be connected first)
        if method_name == "disconnect":
            p4.connect()

        # Mock the underlying method to track calls
        original_method = getattr(p4, method_name)
        setattr(p4, method_name, Mock(side_effect=original_method))

        # Mock execute to verify it's called
        original_execute = p4.execute
        execute_mock = AsyncMock(side_effect=original_execute)
        p4.execute = execute_mock

        # Call the async version
        async_method_name = f"a{method_name}"
        async_method = getattr(p4, async_method_name)
        result = await async_method()

        # Verify execute was called exactly once
        assert execute_mock.call_count == 1, f"execute not called for {async_method_name}"

        # Verify the underlying method was called
        mocked_method = getattr(p4, method_name)
        assert mocked_method.call_count == 1, f"{method_name} not called for {async_method_name}"
        mocked_method.assert_called_once_with()

        # For run_tickets, verify result is a list
        if method_name == "run_tickets":
            assert isinstance(result, list)


@pytest.mark.asyncio
async def test_lock_is_acquired_during_simple_wrap_method(p4async_module):
    """Verify that the lock is acquired when calling simple_wrap_methods"""
    p4async = p4async_module
    p4 = p4async.P4Async()

    # Verify lock is not held initially
    assert not p4.lock.locked()

    # Track if connect was called while lock was held
    lock_held_during_connect = False
    original_connect = p4.connect

    def tracked_connect():
        nonlocal lock_held_during_connect
        lock_held_during_connect = p4.lock.locked()
        return original_connect()

    p4.connect = tracked_connect

    # Call aconnect
    await p4.aconnect()

    # Verify the lock was held during the connect call
    assert lock_held_during_connect, "Lock should have been held during connect()"


class TestRunMethod:
    """Test the run() and arun() methods"""

    @pytest.mark.asyncio
    async def test_arun_calls_through_execute_and_sync_run(self, p4async_module):
        """Verify that arun() -> execute() -> sync_run() -> underlying run()"""
        p4async = p4async_module
        p4 = p4async.P4Async()

        # Register a response for the command
        p4.register_response("info", {"userName": "testuser"})

        # Mock execute to verify it's called
        original_execute = p4.execute
        execute_mock = AsyncMock(side_effect=original_execute)
        p4.execute = execute_mock

        # Mock sync_run to verify it's called
        original_sync_run = p4.sync_run
        sync_run_mock = Mock(side_effect=original_sync_run)
        p4.sync_run = sync_run_mock

        # Mock the parent class's run method (the fake P4's run)
        # We can't easily mock the parent class method due to super() behavior
        # Instead, let's verify that sync_run is called correctly, which is sufficient
        # to prove the call chain

        # Call arun
        result = await p4.arun("info")

        # Verify execute was called
        assert execute_mock.call_count == 1, "execute() not called"

        # Verify execute was called with sync_run
        execute_call_args = execute_mock.call_args
        assert execute_call_args[0][0] == p4.sync_run, "execute() should be called with sync_run"

        # Verify sync_run was called
        assert sync_run_mock.call_count == 1, "sync_run() not called"

        # Verify sync_run was called with the command
        sync_run_mock.assert_called_once_with("info")

        # Verify the result is correct (which proves super().run() was called)
        assert result == {"userName": "testuser"}

    @pytest.mark.asyncio
    async def test_run_with_async_true_calls_through_execute_and_sync_run(self, p4async_module):
        """Verify that run(with_async=True) -> execute() -> sync_run() -> underlying run()"""
        p4async = p4async_module
        p4 = p4async.P4Async()

        # Register a response for the command
        p4.register_response("changes", [{"change": "12345"}])

        # Mock execute to verify it's called
        original_execute = p4.execute
        execute_mock = AsyncMock(side_effect=original_execute)
        p4.execute = execute_mock

        # Mock sync_run to verify it's called
        original_sync_run = p4.sync_run
        sync_run_mock = Mock(side_effect=original_sync_run)
        p4.sync_run = sync_run_mock

        # Call run with with_async=True
        result = await p4.run("changes", with_async=True)

        # Verify execute was called
        assert execute_mock.call_count == 1, "execute() not called"

        # Verify execute was called with sync_run
        execute_call_args = execute_mock.call_args
        assert execute_call_args[0][0] == p4.sync_run, "execute() should be called with sync_run"

        # Verify sync_run was called
        assert sync_run_mock.call_count == 1, "sync_run() not called"

        # Verify sync_run was called with the command (with_async is NOT passed to sync_run)
        sync_run_mock.assert_called_once_with("changes")

        # Verify the result is correct (which proves super().run() was called)
        assert result == [{"change": "12345"}]

    @pytest.mark.asyncio
    async def test_run_with_async_true_passes_arguments(self, p4async_module):
        """Verify that arguments are passed through the call chain"""
        p4async = p4async_module
        p4 = p4async.P4Async()

        # Register a response
        p4.register_response("fstat", [{"depotFile": "//depot/file.txt"}])

        # Mock sync_run to verify arguments
        original_sync_run = p4.sync_run
        sync_run_mock = Mock(side_effect=original_sync_run)
        p4.sync_run = sync_run_mock

        # Call run with multiple arguments
        result = await p4.run("fstat", "-T", "depotFile", "//depot/...", with_async=True)

        # Verify sync_run was called with all arguments
        sync_run_mock.assert_called_once_with("fstat", "-T", "depotFile", "//depot/...")


class TestExecuteAndWrapping:
    """Test the execute() method and wrapping behavior"""

    @pytest.mark.asyncio
    async def test_execute_receives_wrapped_method(self, p4async_module):
        """Verify that execute() receives a properly wrapped method"""
        p4async = p4async_module
        p4 = p4async.P4Async()

        # Track what gets passed to execute
        execute_args = []

        original_execute = p4.execute

        async def mock_execute(func, *args, **kwargs):
            execute_args.append((func, args, kwargs))
            return await original_execute(func, *args, **kwargs)

        p4.execute = mock_execute

        # Call aconnect
        await p4.aconnect()

        # Verify execute was called with a callable
        assert len(execute_args) == 1
        func, args, kwargs = execute_args[0]
        assert callable(func)
        # The wrapped function preserves the original name due to @functools.wraps
        assert func.__name__ == "connect" or func.__name__ == "helper"
        assert len(args) == 0  # aconnect takes no args

    @pytest.mark.asyncio
    async def test_simple_wrap_method_with_arguments(self, p4async_module):
        """Test that arguments are properly passed through the call chain"""
        p4async = p4async_module
        p4 = p4async.P4Async()

        # Add a test method to simple_wrap_methods
        p4.simple_wrap_methods.add("test_method")

        # Create a mock method that accepts arguments
        def test_method(arg1, arg2, kwarg1=None):
            return f"called with {arg1}, {arg2}, {kwarg1}"

        p4.test_method = Mock(side_effect=test_method)

        # Call the async version
        result = await p4.atest_method("value1", "value2", kwarg1="value3")

        # Verify the underlying method was called with correct arguments
        p4.test_method.assert_called_once_with("value1", "value2", kwarg1="value3")
        assert result == "called with value1, value2, value3"

    @pytest.mark.asyncio
    async def test_execute_runs_in_thread_pool(self, p4async_module):
        """Verify that execute() actually runs the function in a thread pool"""
        p4async = p4async_module
        p4 = p4async.P4Async()

        # Track the thread ID where the connect method runs
        import threading

        main_thread_id = threading.get_ident()
        execution_thread_id = None

        original_connect = p4.connect

        def tracked_connect():
            nonlocal execution_thread_id
            execution_thread_id = threading.get_ident()
            return original_connect()

        p4.connect = tracked_connect

        # Call aconnect
        await p4.aconnect()

        # Verify it ran in a different thread
        assert execution_thread_id is not None
        assert execution_thread_id != main_thread_id

    @pytest.mark.asyncio
    async def test_wrap_lock_ensures_lock_is_released(self, p4async_module):
        """Verify that wrap_lock properly releases the lock even on exception"""
        p4async = p4async_module
        p4 = p4async.P4Async()

        # Create a method that raises an exception
        def failing_method():
            raise ValueError("Test exception")

        p4.failing_method = failing_method
        p4.simple_wrap_methods.add("failing_method")

        # Verify lock is not held initially
        assert not p4.lock.locked()

        # Call the async version and expect an exception
        with pytest.raises(ValueError, match="Test exception"):
            await p4.afailing_method()

        # Verify lock was released even after exception
        assert not p4.lock.locked()


class TestRunWrapMethods:
    """Test that run_wrap_methods properly delegate to run() with with_async=True"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method_name", RUN_WRAP_METHODS)
    async def test_async_method_calls_sync_method_which_calls_run(
        self, p4async_module, method_name
    ):
        """Verify that async wrapper -> sync method -> run(with_async=True)"""
        p4async = p4async_module
        p4 = p4async.P4Async()

        # Register appropriate responses for methods that need them
        if "submit" in method_name or "shelve" in method_name:
            p4.register_response(
                "submit" if "submit" in method_name else "shelve", {"status": "ok"}
            )
        elif "login" in method_name:
            p4.register_response("login", {"status": "ok"})
        elif "password" in method_name:
            p4.register_response("password", {"status": "ok"})
        elif "filelog" in method_name:
            p4.register_response("filelog", [{"depotFile": "//depot/file.txt"}])
        elif "print" in method_name:
            p4.register_response("print", [{"depotFile": "//depot/file.txt"}])
        elif "resolve" in method_name:
            p4.register_response("resolve", [{"status": "ok"}])

        # Mock BOTH the sync method AND run() to verify the full chain
        original_method = getattr(p4, method_name)
        method_mock = Mock(side_effect=original_method)
        setattr(p4, method_name, method_mock)

        original_run = p4.run
        run_mock = Mock(side_effect=original_run)
        p4.run = run_mock

        # Call the async version
        async_method_name = f"a{method_name}"
        async_method = getattr(p4, async_method_name)

        # Call with some test arguments (method-specific)
        if "password" in method_name:
            result = await async_method("oldpass", "newpass")
        else:
            result = await async_method()

        # Verify the sync method (e.g., run_login) was called
        assert method_mock.call_count == 1, f"{method_name} not called for {async_method_name}"

        # Verify that with_async=True was passed to the sync method
        method_call_kwargs = method_mock.call_args.kwargs
        assert "with_async" in method_call_kwargs, f"with_async not passed to {method_name}"
        assert method_call_kwargs["with_async"] is True, f"with_async is not True for {method_name}"

        # Verify run() was called (by the sync method)
        assert run_mock.call_count >= 1, f"run() not called by {method_name}"

        # Verify that run() was called WITH with_async=True
        # The sync method receives with_async=True and passes it through to run()
        found_with_async = False
        for call in run_mock.call_args_list:
            if "with_async" in call.kwargs and call.kwargs["with_async"] is True:
                found_with_async = True
                break

        assert found_with_async, f"run() should receive with_async=True from {method_name}"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method_name,args,kwargs",
        [
            ("run_submit", ("arg1",), {}),
            ("run_shelve", ("arg1", "arg2"), {}),
            ("delete_shelve", ("changelist",), {}),
            ("run_login", (), {}),
            ("run_password", ("old", "new"), {}),
        ],
    )
    async def test_run_wrap_methods_pass_arguments_correctly(
        self, p4async_module, method_name, args, kwargs
    ):
        """Verify that arguments are passed correctly through run_wrap_methods"""
        p4async = p4async_module
        p4 = p4async.P4Async()

        # Register appropriate responses
        if "submit" in method_name or "shelve" in method_name:
            p4.register_response(
                "submit" if "submit" in method_name else "shelve", {"status": "ok"}
            )
        elif "login" in method_name:
            p4.register_response("login", {"status": "ok"})
        elif "password" in method_name:
            p4.register_response("password", {"status": "ok"})

        # Mock run() to verify arguments are passed through correctly
        original_run = p4.run
        run_mock = Mock(side_effect=original_run)
        p4.run = run_mock

        # Call the async version with provided arguments
        async_method_name = f"a{method_name}"
        async_method = getattr(p4, async_method_name)
        result = await async_method(*args, **kwargs)

        # Verify run() was called (it will be called by the sync method)
        assert run_mock.call_count >= 1, f"run() not called for {async_method_name}"

        # Verify with_async=True was passed to at least one call
        found_with_async = any(
            call.kwargs.get("with_async") is True for call in run_mock.call_args_list
        )
        assert found_with_async, f"run() was not called with with_async=True for {method_name}"


class TestDeprecated:
    """Tests that may be superseded by the parametrized version but kept for reference"""

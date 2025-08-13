import asyncio
import threading
from typing import Any, Callable, Set, Type, Awaitable, Optional, Union
import P4


class p4async(P4.P4):
    """
    An async extension to P4.P4.
    This class is a placeholder for future async methods.
    """

    # Methods that are simply wrapped to a thread for async execution
    simple_wrap_methods: Set[str] = {
        "connect",
        "disconnect",
        "run_tickets",
    }

    run_wrap_methods: Set[str] = {
        "run_submit",
        "run_shelve",
        "delete_shelve",
        "run_login",
        "run_password",
        "run_filelog",
        "run_print",
        "run_resolve",
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()

    async def _run_blocking(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """
        Default method to run a blocking Perforce command.
        Override this method for customized thread scheduling.
        """

        def helper():
            # Ensure thread safety: the P4 adapter can only have one operation at a time.
            with self.lock:
                return func(*args, **kwargs)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, helper)

    def run(
        self, *args: Any, with_async: bool = False, **kwargs: Any
    ) -> Union[Any, Awaitable[Any]]:
        """
        Run a Perforce command, optionally asynchronously.
        """
        if with_async:
            # return an awaitable
            return self._run_blocking(self.do_run, *args, **kwargs)
        else:
            # execute directly
            return self.do_run(*args, **kwargs)

    def do_run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Run a Perforce command.
        Override this method in a child class to customize the behavior of run further.
        """
        return super().run(*args, **kwargs)

    async def arun(self, *args: Any, **kwargs: Any) -> Any:
        """
        Asynchronous run method.
        """
        return await self._run_blocking(self.do_run, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("arun_"):
            cmd = name[len("arun_") :]
            return lambda *args, **kargs: self.arun(cmd, *args, **kargs)
        elif name.startswith("adelete_"):
            cmd = name[len("adelete_") :]
            return lambda *args, **kargs: self.arun(cmd, "-d", *args, **kargs)
        elif name.startswith("afetch_"):
            cmd = name[len("afetch_") :]
            return lambda *args, **kargs: self.__afetch(cmd, *args, **kargs)
        elif name.startswith("asave_"):
            cmd = name[len("asave_") :]
            return lambda *args, **kargs: self.__asave(cmd, *args, **kargs)
        elif name.startswith("aiterate_"):
            cmd = name[len("aiterate_") :]
            return lambda *args, **kargs: self.__aiterate(cmd, *args, **kargs)
        if name.startswith("a") and name[1:] in self.simple_wrap_methods:
            method = name[1:]
            return lambda *args, **kwargs: self._run_blocking(
                getattr(self, method), *args, **kwargs
            )
        elif name.startswith("a") and name[1:] in self.run_wrap_methods:
            method = name[1:]
            return lambda *args, **kwargs: getattr(self, method)(
                *args, with_async=True, **kwargs
            )
        return super().__getattr__(name)

    async def __afetch(self, cmd: str, *args: Any, **kargs: Any) -> Any:
        """
        Handle async versions of fetch commands.
        """
        result = await self.arun(cmd, "-o", *args, **kargs)
        for r in result:
            if isinstance(r, tuple) or isinstance(r, dict):
                return r
        return result[0]

    async def __aiterate(self, cmd: str, *args: Any, **kargs: Any):
        """
        Handle async versions of iterate commands.
        """
        if cmd not in self.specfields:
            raise Exception("Unknown spec list command: %s", cmd)

        specs = await self.arun(cmd, *args, **kargs)
        spec = self.specfields[cmd][0]
        field = self.specfields[cmd][1]
        for spec in specs:
            yield await self.arun(spec, "-o", spec[field])[0]

    async def __asave(self, cmd: str, *args: Any, **kargs: Any) -> Any:
        self.input = args[0]
        return await self.arun(cmd, "-i", args[1:], **kargs)

    async def __aenter__(self) -> "P4Async":
        """
        Asynchronous context manager enter method.
        """
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """
        Asynchronous context manager exit method.
        """
        if self.connected():
            await self.adisconnect()

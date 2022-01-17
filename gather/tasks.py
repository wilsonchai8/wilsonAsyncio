from futures import Future

class Task(Future):
    
    def __init__(self, coro, loop=None):
        super().__init__(loop=loop)
        self._coro = coro
        self._loop.call_soon(self.__step)

    def __wakeup(self, future):
        try:
            future.result()
        except Exception as exc:
            raise exc
        else:
            self.__step()
        self = None

    def __step(self, exc=None):
        coro = self._coro
        try:
            if exc is None:
                result = coro.send(None)
            else:
                result = coro.throw(exc)
        except StopIteration as exc:
            super().set_result(exc.value)
        else:
            blocking = getattr(result, '_asyncio_future_blocking', None)
            if blocking:
                result._asyncio_future_blocking = False
                result.add_done_callback(self.__wakeup, result)
        finally:
            self = None

def ensure_future(coro_or_future, *, loop=None):
    if isinstance(coro_or_future, Future):
        return coro_or_future
    else:
        return loop.create_task(coro_or_future)


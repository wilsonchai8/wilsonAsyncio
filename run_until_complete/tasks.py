from futures import *

class Task(Future):
    
    def __init__(self, coro, loop=None):
        super().__init__(loop=loop)
        self._coro = coro
        self._loop.call_soon(self.__step)

    def __step(self, exc=None):
        coro = self._coro
        try:
            if exc is None:
                coro.send(None)
            else:
                coro.throw(exc)
        except StopIteration as exc:
            super().set_result(exc.value)
        finally:
            self = None

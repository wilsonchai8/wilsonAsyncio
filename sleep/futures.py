

_PENDING = 'PENDING'
_FINISHED = 'FINISHED'


class Future:

    _state = _PENDING
    _result = None
    _loop = None
    _asyncio_future_blocking = False

    def __init__(self, *, loop=None):
        self._loop = loop
        self._callbacks = []

    def add_done_callback(self, fn, *args):
        if self._state != _PENDING:
            self._loop.call_soon(fn, *args)
        else:
            self._callbacks.append((fn, *args))

    def set_result(self, result):
        self._result = result
        self._state = _FINISHED
        self.__schedule_callbacks()

    def __schedule_callbacks(self):
        for callback in self._callbacks:
            fn = callback[0]
            args = callback[1] if len(callback) > 1 else None
            self._loop.call_soon(fn, args)

    def result(self):
        return self._result

    def __await__(self):
        if self._state == _PENDING:
            self._asyncio_future_blocking = True
            yield self
        return self.result()

    __iter__ = __await__


def set_result_unless_cancelled(fut, result):
    fut.set_result(result)
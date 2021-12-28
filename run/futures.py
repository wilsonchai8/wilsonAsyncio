

_PENDING = 'PENDING'
_FINISHED = 'FINISHED'


class Future:

    _state = _PENDING
    _result = None
    _loop = None

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
        callbacks = self._callbacks[:]
        for callback, args in callbacks:
            self._loop.call_soon(callback, args)

    def result(self):
        return self._result
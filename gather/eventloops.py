import collections
import tasks 
from futures import Future

_event_loop = None

def _complete_eventloop(fut):
    fut._loop.stop()

def get_event_loop():
    global _event_loop
    if _event_loop is None:
        _event_loop = Eventloop()
    return _event_loop

class Eventloop:

    def __init__(self):
        self._ready = collections.deque()
        self._stopping = False

    def stop(self):
        self._stopping = True

    def call_soon(self, callback, *args):
        handle = Handle(callback, *args)
        self._ready.append(handle)

    def run_once(self):
        ntodo = len(self._ready)
        for _ in range(ntodo):
            handle = self._ready.popleft()
            handle._run()

    def run_forever(self):
        while True:
            self.run_once()
            if self._stopping:
                break

    def run_until_complete(self, future):
        future = tasks.ensure_future(future, loop=self)
        future.add_done_callback(_complete_eventloop, future)
        self.run_forever()
        return future.result()

    def create_task(self, coro):
        task = tasks.Task(coro, loop=self)
        return task


class Handle:

    def __init__(self, callback, *args):
        self._callback = callback
        self._args = args

    def _run(self):
        self._callback(*self._args)


def gather(*coros_or_futures, loop=None):
    loop = get_event_loop()

    def _done_callback(fut):
        nonlocal nfinished
        nfinished += 1

        if nfinished == nfuts:
            results = []
            for fut in children:
                res = fut.result()
                results.append(res)

            outer.set_result(results)

    children = []
    nfuts = 0
    nfinished = 0

    for arg in coros_or_futures:
        fut = tasks.ensure_future(arg, loop=loop)
        nfuts += 1
        fut.add_done_callback(_done_callback)

        children.append(fut)

    outer = _GatheringFuture(children, loop=loop)
    return outer


class _GatheringFuture(Future):

    def __init__(self, children, *, loop=None):
        super().__init__(loop=loop)
        self._children = children

def run(main):
    loop = get_event_loop()
    return loop.run_until_complete(main)
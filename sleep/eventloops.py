import collections
import tasks
from futures import Future, set_result_unless_cancelled
import time
import selectors
import socket
import heapq

_event_loop = None


def _complete_eventloop(fut):
    fut._loop.stop()


def get_event_loop():
    global _event_loop
    if _event_loop is None:
        _event_loop = Eventloop()
    return _event_loop


def fake_socket():
    sel = selectors.DefaultSelector()
    _ssock, _ = socket.socketpair()
    _ssock.setblocking(False)
    sel.register(_ssock.fileno(), selectors.EVENT_READ, None)
    return sel

class Eventloop:

    def __init__(self):
        self._ready = collections.deque()
        self._scheduled = []
        self._stopping = False
        self._selector = fake_socket()

    def stop(self):
        self._stopping = True

    def current_time(self):
        return time.monotonic()

    def call_soon(self, callback, *args):
        handle = Handle(callback, *args)
        self._ready.append(handle)

    def call_later(self, delay, callback, *args):
        timer = self.call_at(self.current_time() + delay, callback, *args)
        return timer

    def call_at(self, when, callback, *args):
        timer = TimerHandle(when, callback, *args)
        heapq.heappush(self._scheduled, timer)
        return timer

    def run_once(self):
        timeout = 0
        if not self._ready and self._scheduled:
            heapq.heapify(self._scheduled)
            when = self._scheduled[0]._when
            timeout = min(max(0, when - self.current_time()), 60)
        self._selector.select(timeout)

        end_time = self.current_time()
        while self._scheduled:
            handle = self._scheduled[0]
            if handle._when >= end_time:
                break
            handle = heapq.heappop(self._scheduled)
            self._ready.append(handle)
        

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

    def create_future(self):
        return Future(loop=self) 


class Handle:

    def __init__(self, callback, *args):
        self._callback = callback
        self._args = args

    def _run(self):
        self._callback(*self._args)


class TimerHandle(Handle):
    
    def __init__(self, when, callback, *args):
        super().__init__(callback, *args)
        self._when = when

    def __lt__(self, other):
        return self._when < other._when

    def __gt__(self, other):
        return self._when > other._when

    def __eq__(self, other):
        return self._when > other._when

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
        self._cancel_requested = False

def run(main):
    loop = get_event_loop()
    return loop.run_until_complete(main)


async def sleep(delay, result=None, *, loop=None):
    if loop is None:
        loop = get_event_loop()
    future = loop.create_future()
    loop.call_later(delay, set_result_unless_cancelled, future, result)
    await future

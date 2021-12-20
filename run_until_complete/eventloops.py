import collections
import tasks


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
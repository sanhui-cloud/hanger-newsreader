import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class _TaskResult:
    on_done: Optional[Callable]
    on_error: Optional[Callable]
    result: Any
    error: Optional[Exception]


@dataclass
class _StatusMsg:
    message: str
    callback: Callable[[str], None]


class BackgroundTaskManager:
    """
    Wraps a ThreadPoolExecutor and bridges results back to the GUI thread
    via queue.Queue + widget.after() polling.
    Zero widget manipulation from worker threads.
    """

    def __init__(self, gui_root, max_workers: int = 8):
        self._executor = ThreadPoolExecutor(max_workers=max_workers,
                                             thread_name_prefix='news-worker')
        self._queue: queue.Queue[_TaskResult | _StatusMsg] = queue.Queue()
        self._root = gui_root
        self._poll()

    def submit(
        self,
        fn: Callable,
        *args,
        on_done: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        **kwargs,
    ) -> None:
        """Submit fn(*args, **kwargs) to thread pool. Callbacks fire on GUI thread."""
        def _wrapper():
            try:
                result = fn(*args, **kwargs)
                self._queue.put(_TaskResult(on_done, on_error, result, None))
            except Exception as e:
                self._queue.put(_TaskResult(on_done, on_error, None, e))

        self._executor.submit(_wrapper)

    def post_status(self, message: str, callback: Callable[[str], None]) -> None:
        """Post a status message from a worker thread to be delivered on the GUI thread."""
        self._queue.put(_StatusMsg(message, callback))

    def _poll(self) -> None:
        try:
            while True:
                item = self._queue.get_nowait()
                if isinstance(item, _StatusMsg):
                    item.callback(item.message)
                elif isinstance(item, _TaskResult):
                    if item.error is not None:
                        if item.on_error:
                            item.on_error(item.error)
                    else:
                        if item.on_done:
                            item.on_done(item.result)
        except queue.Empty:
            pass
        self._root.after(100, self._poll)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

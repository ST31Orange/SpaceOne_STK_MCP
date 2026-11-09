"""A single-threaded COM apartment.

STK's automation objects are apartment-bound. Every COM call in this package is
therefore marshalled to one long-lived thread, which also owns the STK
application object. This avoids the "RPC server unavailable" failures that
happen when different FastAPI thread-pool workers touch the same COM proxy.
"""

from __future__ import annotations

import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Callable, TypeVar

from .errors import StkTimeoutError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ComWorker:
    def __init__(self, name: str = "stk-com") -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=name)
        self._local = threading.local()
        self._thread: threading.Thread | None = None
        self._closed = False

    @property
    def available(self) -> bool:
        return sys.platform == "win32"

    def run(self, fn: Callable[[], T], *, timeout: float | None = None) -> T:
        if self._closed:
            raise RuntimeError("COM worker has been shut down")
        # A tool handler already runs inside the apartment; calling run() again
        # must execute inline instead of deadlocking on the single worker.
        if threading.current_thread() is self._thread:
            return fn()
        future = self._executor.submit(self._invoke, fn)
        try:
            return future.result(timeout=timeout)
        except FutureTimeout as exc:
            raise StkTimeoutError(
                f"STK operation did not finish within {timeout} seconds",
                hint="Reduce the time span or increase STK_MCP_REQUEST_TIMEOUT.",
            ) from exc

    def _invoke(self, fn: Callable[[], T]) -> T:
        if self._thread is None:
            self._thread = threading.current_thread()
        if not getattr(self._local, "initialized", False):
            if sys.platform != "win32":
                raise RuntimeError("STK COM automation is only available on Windows")
            import pythoncom

            pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
            self._local.initialized = True
            self._local.pythoncom = pythoncom
        return fn()

    def shutdown(self) -> None:
        self._closed = True
        try:
            self._executor.submit(self._release).result(timeout=10)
        except Exception:
            logger.debug("COM worker release failed", exc_info=True)
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _release(self) -> None:
        pythoncom = getattr(self._local, "pythoncom", None)
        if pythoncom is not None:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
        self._local.initialized = False

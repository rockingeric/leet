import threading  # practicing Condition instead of queue.Queue
from contextlib import contextmanager
from collections import deque
import time


class PoolTimeout(Exception):
    """Raised when acquiring a connection times out."""

    def __init__(self, *args):
        super().__init__(*args)


class PoolClosed(Exception):
    """Raised when acquiring from a closed pool."""

    def __init__(self, *args):
        super().__init__(*args)


class DatabaseConn:
    def __init__(self):
        self.closed = False

    def query(self):
        return "Querying the DB"

    def close(self):
        self.closed = True


class ConnectionPool:
    def __init__(self, factory, max_size, timeout=None):
        self._cond = threading.Condition()
        self._is_closed = False
        self._available = deque()
        self._checked_out = set()
        self._factory = factory
        self._max_size = max_size
        self._timeout = timeout

        for _ in range(max_size):
            self._available.append(factory())

    def acquire(self, timeout=None):
        if timeout is None:
            timeout = self._timeout

        deadline = None if timeout is None else time.monotonic() + timeout

        with self._cond:
            while not self._available:
                if self._is_closed:
                    raise PoolClosed("Cannot acquire, Pool Closed")

                time_left = None if deadline is None else deadline - time.monotonic()
                if time_left is not None and time_left <= 0:
                    raise PoolTimeout(f"no connection available within {timeout}s")

                self._cond.wait(time_left)

            if self._is_closed:
                raise PoolClosed("Cannot acquire, Pool Closed")

            conn = self._available.popleft()
            self._checked_out.add(conn)
            return conn

    @staticmethod
    def _close_conn(conn):
        """Close conn if it has a close() method."""
        close = getattr(conn, "close", None)
        if callable(close):
            close()

    def release(self, conn):
        """Returns an object back to the pool, or closes it if the pool is closed."""
        with self._cond:
            if conn not in self._checked_out:
                raise ValueError("connection is not checked out (double release?)")

            self._checked_out.discard(conn)

            if self._is_closed:
                self._close_conn(conn)
                return

            self._available.append(conn)
            self._cond.notify()

    def close(self):
        """Close the pool. Idle conns close now, checked-out ones close on release()."""
        with self._cond:
            if self._is_closed:
                return

            self._is_closed = True

            idle, self._available = list(self._available), deque()

            self._cond.notify_all()

        for conn in idle:
            self._close_conn(conn)

    def get_current_connections_count(self):
        with self._cond:
            return len(self._checked_out)

    @contextmanager
    def borrow(self):
        """Context manager to ensure safe acquisition and release."""
        obj = self.acquire()
        try:
            yield obj
        finally:
            self.release(obj)

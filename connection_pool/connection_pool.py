import threading  # practicing Condition instead of queue.Queue
from contextlib import contextmanager
from collections import deque
import time


class PoolTimeout(Exception):
    """Raised when acquiring a connection times out."""
    pass


class PoolClosed(Exception):
    """Raised when acquiring from a closed pool."""
    pass


class DatabaseConn:
    def __init__(self):
        self.closed = False

    def query(self):
        return "Querying the DB"

    def close(self):
        self.closed = True


class ConnectionLease:
    def __init__(self, pool, conn):
        self._pool = pool
        self._conn = conn
        self._released = False

    def __enter__(self):
        return self._conn

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def close(self):
        if not self._released:
            self._released = True
            self._pool.release(self)

    @property
    def conn(self):
        return self._conn


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
            while True:
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
                if not self._is_conn_healthy(conn):
                    self._close_conn(conn)

                    conn = self._factory()
                    if not self._is_conn_healthy(conn):
                        self._close_conn(conn)
                        continue

                self._checked_out.add(conn)
                return ConnectionLease(self, conn)

    @staticmethod
    def _is_conn_healthy(conn):
        if getattr(conn, "closed", False):
            return False

        health_check = getattr(conn, "is_healthy", None)
        if callable(health_check):
            try:
                return bool(health_check())
            except Exception:
                return False

        ping = getattr(conn, "ping", None)
        if callable(ping):
            try:
                ping()
                return True
            except Exception:
                return False

        return True

    @staticmethod
    def _close_conn(conn):
        """Close conn if it has a close() method."""
        close = getattr(conn, "close", None)
        if callable(close):
            close()

    def release(self, conn):
        """Returns an object back to the pool, or closes it if the pool is closed."""
        raw_conn = conn.conn if isinstance(conn, ConnectionLease) else conn

        with self._cond:
            if raw_conn not in self._checked_out:
                raise ValueError("connection is not checked out (double release?)")

            self._checked_out.discard(raw_conn)

            if self._is_closed:
                self._close_conn(raw_conn)
                self._cond.notify_all()
                return

            self._available.append(raw_conn)
            self._cond.notify()

    def close(self, drain=False, timeout=None):
        """Close the pool.

        Idle conns close now. Checked-out ones close on release(). If drain=True,
        wait for checked-out conns to return before finishing close().
        """
        deadline = None if timeout is None else time.monotonic() + timeout

        with self._cond:
            if self._is_closed:
                return

            self._is_closed = True

            idle, self._available = list(self._available), deque()

            self._cond.notify_all()

            if drain:
                while self._checked_out:
                    time_left = None if deadline is None else deadline - time.monotonic()
                    if time_left is not None and time_left <= 0:
                        raise PoolTimeout("timed out while draining pool")
                    self._cond.wait(time_left)

        for conn in idle:
            self._close_conn(conn)

    def get_current_connections_count(self):
        with self._cond:
            return len(self._checked_out)

    @contextmanager
    def borrow(self):
        """Context manager to ensure safe acquisition and release."""
        with self.acquire() as conn:
            yield conn

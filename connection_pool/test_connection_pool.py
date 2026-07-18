import threading
import time

import pytest

from connection_pool import DatabaseConn, ConnectionPool, PoolClosed, PoolTimeout


def test_max_size():
    pool = ConnectionPool(factory=DatabaseConn, max_size=3, timeout=2)

    with pool.acquire() as resource:
        assert resource.query() == "Querying the DB"

    lease1 = pool.acquire()
    lease2 = pool.acquire()
    lease3 = pool.acquire()

    assert lease1.query() == "Querying the DB"
    assert lease2.query() == "Querying the DB"
    assert lease3.query() == "Querying the DB"

    with pytest.raises(PoolTimeout):
        pool.acquire()


def test_checkout_replaces_closed_connection():
    pool = ConnectionPool(factory=DatabaseConn, max_size=2, timeout=2)

    lease = pool.acquire()
    original = lease.conn
    pool.release(lease)

    original.closed = True

    with pool.acquire() as replacement:
        assert replacement is not original
        assert not replacement.closed


def test_close_can_drain_checked_out_connections():
    pool = ConnectionPool(factory=DatabaseConn, max_size=1, timeout=2)

    lease = pool.acquire()

    def release_later():
        time.sleep(0.05)
        pool.release(lease)

    thread = threading.Thread(target=release_later)
    thread.start()

    pool.close(drain=True, timeout=1)

    thread.join()

    assert lease.closed


def test_closed_pool_cant_be_acquired():
    pool = ConnectionPool(factory=DatabaseConn, max_size=3, timeout=2)

    with pool.borrow() as resource:
        assert resource.query() == "Querying the DB"

    lease = pool.acquire()
    assert lease.query() == "Querying the DB"

    pool.close()

    assert not lease.closed

    with pytest.raises(PoolClosed):
        pool.acquire()

    pool.release(lease)
    assert lease.closed


def test_double_release():
    pool = ConnectionPool(factory=DatabaseConn, max_size=3, timeout=2)

    lease = pool.acquire()
    pool.release(lease)

    with pytest.raises(ValueError):
        pool.release(lease)


def test_crowd_connections():
    pool = ConnectionPool(factory=DatabaseConn, max_size=3, timeout=5)
    results = []
    errors = []
    start = threading.Barrier(100)

    def grab():
        try:
            start.wait()
            for _ in range(20):
                with pool.borrow():
                    results.append(pool.get_current_connections_count())
                    time.sleep(0.001)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=grab) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"threads failed: {errors[:3]}"
    assert max(results) <= 3, f"exceeded 3 simultaneous connections: saw {max(results)}"
    assert 3 in results, "pool never fully used"


def test_no_sharing():
    pool = ConnectionPool(factory=DatabaseConn, max_size=3, timeout=5)
    errors = []
    held = set()
    held_lock = threading.Lock()
    start = threading.Barrier(100)

    def grab():
        try:
            start.wait()
            for _ in range(20):
                with pool.borrow() as conn:
                    cid = id(conn)
                    with held_lock:
                        if cid in held:
                            raise AssertionError(
                                f"connection {cid} handed to two threads"
                            )
                        held.add(cid)
                    time.sleep(0.001)
                    with held_lock:
                        held.discard(cid)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=grab) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"threads failed: {errors[:3]}"

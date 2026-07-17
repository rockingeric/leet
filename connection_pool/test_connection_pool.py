from connection_pool import DatabaseConn, ConnectionPool, PoolTimeout, PoolClosed
import threading
import time

def test_max_size():
    # 1. Create a pool of 3 expensive resources
    pool = ConnectionPool(factory=DatabaseConn, max_size=3, timeout=2)

    # 2. Use a context manager to borrow and automatically return objects
    with pool.borrow() as resource:
        print(resource.query())

    # 3. Manually acquire all three, exhausting the pool
    res = pool.acquire()
    res1 = pool.acquire()
    res2 = pool.acquire()

    print(res.query())
    print(res1.query())
    print(res2.query())

    acquire_error = False
    try:
        res3 = pool.acquire()
        print(res3.query())
    except PoolTimeout:
        acquire_error = True

    assert acquire_error

    print("OK")


def test_closed_pool_cant_be_acquired():
    # 1. Create a pool of 3 expensive resources
    pool = ConnectionPool(factory=DatabaseConn, max_size=3, timeout=2)

    # 2. Use a context manager to borrow and automatically return objects
    with pool.borrow() as resource:
        print(resource.query())

    # 3. Acquire one, kept checked out across close()
    res = pool.acquire()
    print(res.query())

    pool.close()

    # Graceful: idle conns closed immediately; the checked-out one is left alone.
    assert not res.closed

    acquire_in_closed_error = False
    try:
        res3 = pool.acquire()
        print(res3.query())
    except PoolClosed:
        acquire_in_closed_error = True

    assert acquire_in_closed_error

    # Returning the in-use conn after close shuts it down instead of re-queuing.
    pool.release(res)
    assert res.closed

    print("OK")


def test_double_release():
    pool = ConnectionPool(factory=DatabaseConn, max_size=3, timeout=2)

    res = pool.acquire()
    pool.release(res)

    double_release_error = False
    try:
        pool.release(res)
    except ValueError:
        double_release_error = True

    assert double_release_error
    print("OK")


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
                    time.sleep(0.001)  # hold briefly so threads overlap
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=grab) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"threads failed: {errors[:3]}"
    assert max(results) <= 3, f"exceeded 3 simultaneous connections: saw {max(results)}"
    assert 3 in results, "pool never fully used"
    print("OK")


def test_no_sharing():
    pool = ConnectionPool(factory=DatabaseConn, max_size=3, timeout=5)
    errors = []
    held = set()  # ids of connections held right now
    held_lock = threading.Lock()
    start = threading.Barrier(100)

    def grab():
        try:
            start.wait()
            for _ in range(20):
                with pool.borrow() as conn:
                    cid = id(conn)
                    with held_lock:
                        if cid in held:  # someone else already holds this exact conn
                            raise AssertionError(
                                f"connection {cid} handed to two threads"
                            )
                        held.add(cid)
                    time.sleep(0.001)  # hold briefly so threads overlap
                    with held_lock:
                        held.discard(cid)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=grab) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"threads failed: {errors[:3]}"
    print("OK")


if __name__ == "__main__":
    test_max_size()
    test_closed_pool_cant_be_acquired()
    test_double_release()
    test_crowd_connections()
    test_no_sharing()

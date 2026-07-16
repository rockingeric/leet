import time
import threading

from token_bucket import TokenBucket


# --- Invariant: refill never pushes the bucket past its capacity ceiling ---
def test_capacity_ceiling():
    bucket = TokenBucket(5, 1, 0.05)

    assert bucket.consume(5)

    time.sleep(0.5)                  # >> 5 periods of refill, but capped at capacity

    assert bucket.consume(5)
    assert bucket.consume() is False


# --- Invariant: a denied request spends nothing (all-or-nothing) ---
def test_denial_spends_nothing():
    bucket = TokenBucket(5, 1, 2)

    assert bucket.consume(10) is False
    assert bucket.consume(2)


# --- Adversarial: max contention must not over-grant beyond capacity ---
def test_thread_safe():
    # refill_period 3600 => no refill during a sub-second test
    bucket = TokenBucket(50, 1, 3600)
    results = []                     # list.append is atomic in CPython, no lock needed
    start = threading.Barrier(100)   # release all threads at once => max contention

    def grab():
        start.wait()
        results.append(bucket.consume(1))

    threads = [threading.Thread(target=grab) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    granted = sum(results)           # True == 1
    assert granted == 50, f"expected 50 grants, got {granted}"

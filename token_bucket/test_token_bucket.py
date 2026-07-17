import time
import threading

from token_bucket import TokenBucket


def test_capacity_ceiling():
    bucket = TokenBucket(5, 1, 0.05)

    assert bucket.consume(5)

    time.sleep(0.5)                  # well past refill time, but capped at capacity

    assert bucket.consume(5)
    assert bucket.consume() is False


def test_denial_spends_nothing():
    bucket = TokenBucket(5, 1, 2)

    assert bucket.consume(10) is False
    assert bucket.consume(2)


def test_thread_safe():
    # huge refill_period so nothing refills during the test
    bucket = TokenBucket(50, 1, 3600)
    results = []
    start = threading.Barrier(100)   # release all threads at once

    def grab():
        start.wait()
        results.append(bucket.consume(1))

    threads = [threading.Thread(target=grab) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    granted = sum(results)
    assert granted == 50, f"expected 50 grants, got {granted}"

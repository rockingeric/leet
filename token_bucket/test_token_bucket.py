import threading
import time

import pytest

from token_bucket import TokenBucket


@pytest.fixture
def bucket():
    return TokenBucket(5, 1, 2)


@pytest.fixture
def concurrent_bucket():
    return TokenBucket(50, 1, 3600)


def test_capacity_ceiling():
    bucket = TokenBucket(5, 1, 0.05)

    assert bucket.consume(5)

    time.sleep(0.5)

    assert bucket.consume(5)
    assert bucket.consume() is False


def test_denial_spends_nothing(bucket):
    assert bucket.consume(10) is False
    assert bucket.consume(2)


def test_thread_safe(concurrent_bucket):
    results = []
    start = threading.Barrier(100)

    def grab():
        start.wait()
        results.append(concurrent_bucket.consume(1))

    threads = [threading.Thread(target=grab) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    granted = sum(results)
    assert granted == 50, f"expected 50 grants, got {granted}"

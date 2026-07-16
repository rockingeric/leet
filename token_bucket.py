import time
import threading


class TokenBucket:
    def __init__(self, capacity, refill_rate, refill_period):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_period = refill_period
        self.last_refill = time.monotonic()
        self.tokens = self.capacity
        self.lock = threading.Lock()

    def consume(self, number_of_tokens=1):
        if number_of_tokens < 1:
            return False

        with self.lock:

            current_time = time.monotonic()

            # Try to refil
            if self.tokens < self.capacity:
                time_elapsed = current_time - self.last_refill

                if time_elapsed >= self.refill_period:
                    whole_periods, rest = divmod(time_elapsed, self.refill_period)
                    qty_can_refill = whole_periods * self.refill_rate
                    refill_boundary = current_time - rest

                    empty_spots = self.capacity - self.tokens
                    qty_to_refil = min(empty_spots, qty_can_refill)

                    if qty_to_refil > 0:
                        self.last_refill = refill_boundary
                        self.tokens += qty_to_refil

            # Try to retrieve requested tokens
            if self.tokens >= number_of_tokens:
                time.sleep(0.0001)
                self.tokens -= number_of_tokens
            else:
                return False

        return True


def test_capacity_ceiling():
    bucket = TokenBucket(5, 1, 2)

    assert bucket.consume(5)

    time.sleep(20)

    assert bucket.consume(5)
    assert bucket.consume() is False

    print('OK')


def test_denial_spends_nothing():
    bucket = TokenBucket(5, 1, 2)

    assert bucket.consume(10) is False
    assert bucket.consume(2)

    print('OK')


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

    print('OK')


if __name__ == "__main__":
    test_capacity_ceiling()
    test_denial_spends_nothing()
    test_thread_safe()

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
                # Deliberate: widen the critical section so test_thread_safe reliably
                # fails if the lock is ever removed. The GIL would otherwise mask the
                # read-modify-write race on self.tokens.
                time.sleep(0.0001)
                self.tokens -= number_of_tokens
            else:
                return False

        return True

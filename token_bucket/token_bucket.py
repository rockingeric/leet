import threading
import time


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
            if self.tokens < self.capacity:
                time_elapsed = current_time - self.last_refill

                if time_elapsed >= self.refill_period:
                    whole_periods, rest = divmod(time_elapsed, self.refill_period)
                    refill_amount = whole_periods * self.refill_rate
                    refill_boundary = current_time - rest

                    empty_spots = self.capacity - self.tokens
                    tokens_to_add = min(empty_spots, refill_amount)

                    if tokens_to_add > 0:
                        self.last_refill = refill_boundary
                        self.tokens += tokens_to_add

            if self.tokens >= number_of_tokens:
                time.sleep(0.0001)
                self.tokens -= number_of_tokens
            else:
                return False

        return True

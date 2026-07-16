import time
import random

from retry_decorator import retry


# --- Invariant: a failing call is attempted exactly max_attempts times, then re-raises ---
def test_exhaustion_path():
    calls = []

    @retry(max_attempts=2, base=1, multiplier=1.4, allowed_errors=(ConnectionError,))
    def load_users():
        calls.append(1)
        raise ConnectionError

    try:
        load_users()
    except ConnectionError:
        pass

    assert len(calls) == 2


# --- Adversarial: an error outside allowed_errors is not retried, propagates immediately ---
def test_flaky():
    calls = []

    @retry(max_attempts=3, base=0, multiplier=1.4, allowed_errors=(ConnectionError,))
    def load_users():
        calls.append(1)
        raise ValueError

    try:
        load_users()
    except ValueError:
        pass

    assert len(calls) == 1


def test_succeeds_after_retries():
    calls = []

    @retry(max_attempts=3, base=0, multiplier=1.4, allowed_errors=(ConnectionError,))
    def load_users():
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError
        return 'users'

    assert load_users() == 'users'
    assert len(calls) == 3


# --- Invariant: backoff delays match the spec (base * multiplier^n), asserted with jitter stripped ---
def test_backoff_delays():
    sleeps = []
    orig_sleep, orig_uniform = time.sleep, random.uniform
    time.sleep = lambda s: sleeps.append(s)
    random.uniform = lambda a, b: 0.0   # strip jitter -> deterministic
    try:
        @retry(max_attempts=4, base=1, multiplier=2, allowed_errors=(ConnectionError,))
        def always_fails():
            raise ConnectionError

        try:
            always_fails()
        except ConnectionError:
            pass
    finally:
        time.sleep, random.uniform = orig_sleep, orig_uniform

    # 4 attempts -> sleeps after attempts 1,2,3: base*2^0, base*2^1, base*2^2
    assert sleeps == [1, 2, 4], sleeps

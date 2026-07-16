import functools
import time
import random
import logging
logger = logging.getLogger(__name__)


def retry(max_attempts, base, multiplier, allowed_errors):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0

            while True:
                try:
                    return func(*args, **kwargs)
                except allowed_errors:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    wait_in_seconds = base * (multiplier ** (attempt - 1))
                    logger.warning(
                        '%s failed on attempt %d/%d, retrying in %.1fs',
                        func.__name__, attempt, max_attempts, wait_in_seconds,
                    )
                    time.sleep(wait_in_seconds + random.uniform(0, wait_in_seconds))   # "full jitter"

        return wrapper
    return decorator


def test_exaustion_path():
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


if __name__ == '__main__':
    test_exaustion_path()
    test_flaky()
    test_succeeds_after_retries()
    test_backoff_delays()
    print('ok')

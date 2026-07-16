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

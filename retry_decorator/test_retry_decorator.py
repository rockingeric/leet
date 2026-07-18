import time
import random

import pytest

from retry_decorator import retry


def test_exhaustion_path():
    calls = []

    @retry(max_attempts=2, base=1, multiplier=1.4, allowed_errors=(ConnectionError,))
    def load_users():
        calls.append(1)
        raise ConnectionError

    with pytest.raises(ConnectionError):
        load_users()

    assert len(calls) == 2


def test_flaky():
    calls = []

    @retry(max_attempts=3, base=0, multiplier=1.4, allowed_errors=(ConnectionError,))
    def load_users():
        calls.append(1)
        raise ValueError

    with pytest.raises(ValueError):
        load_users()

    assert len(calls) == 1


def test_succeeds_after_retries():
    calls = []

    @retry(max_attempts=3, base=0, multiplier=1.4, allowed_errors=(ConnectionError,))
    def load_users():
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError
        return "users"

    assert load_users() == "users"
    assert len(calls) == 3


def test_backoff_delays(monkeypatch):
    sleeps = []
    monkeypatch.setattr(time, "sleep", lambda seconds: sleeps.append(seconds))
    monkeypatch.setattr(random, "uniform", lambda a, b: 0.0)

    @retry(max_attempts=4, base=1, multiplier=2, allowed_errors=(ConnectionError,))
    def always_fails():
        raise ConnectionError

    with pytest.raises(ConnectionError):
        always_fails()

    assert sleeps == [1, 2, 4]

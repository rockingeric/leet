# Retry Decorator

**Problem.** A decorator `@retry(max_attempts, base, multiplier, allowed_errors)` that
re-runs a function on failure with exponential backoff, retrying only the exceptions you
name and re-raising everything else.

**Design.** A three-level decorator factory: `retry(...)` captures the config, `decorator`
captures the function, `wrapper` runs the attempt loop.

## Invariants
- **Attempt count** — a persistently failing call runs exactly `max_attempts` times, then re-raises.
- **Selective catching** — only `allowed_errors` are retried; any other exception propagates on the first raise.
- **Backoff sequence** — delays follow `base * multiplier^(attempt-1)`: `1, 2, 4, ...`

## Non-obvious decisions
- **`functools.wraps`** preserves the wrapped function's `__name__`, docstring, and
  signature — without it the decorated function masquerades as `wrapper`.
- **Bare `raise`** on exhaustion re-raises the *original* exception with its traceback
  intact, instead of `raise e` which would truncate it.
- **Full jitter** — the sleep is `delay + uniform(0, delay)`, spreading retries across the
  window so a fleet of clients doesn't stampede the backend in lockstep.
- **The delay test asserts spec, not output.** `test_backoff_delays` strips jitter
  (`random.uniform -> 0`), captures the sleeps, and asserts they equal `[1, 2, 4]` computed
  from the formula — not whatever the code happened to emit. A test that just echoes the
  implementation proves nothing.

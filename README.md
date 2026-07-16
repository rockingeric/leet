# senior-python

A collection of concurrency and systems primitives implemented from first principles for
senior-engineer interview prep — machine-coding / low-level-design style. Each component is
built with a spec-first approach and emphasizes **adversarial and invariant tests**, not just
happy-path coverage.

These are **not** production libraries — mature packages like [`tenacity`](https://github.com/jd/tenacity)
already exist. The point is demonstrating the ability to build these primitives and reason
about their correctness.

## Components

| Component | What it is | Key ideas |
|-----------|------------|-----------|
| [`lru_cache/`](lru_cache/) | Fixed-capacity LRU cache | `O(1)` get/put via hash map + doubly linked list; capacity & recency invariants |
| [`token_bucket/`](token_bucket/) | Thread-safe rate limiter | Lazy `divmod` refill, capacity ceiling, lock correct by design not by GIL luck |
| [`retry_decorator/`](retry_decorator/) | Exponential-backoff retry | 3-level decorator factory, `functools.wraps`, traceback-preserving re-raise, full jitter |
| [`connection_pool/`](connection_pool/) | Bounded blocking pool *(in progress)* | Deadline-based blocking acquire, no slot leaks, context-manager release |

Each directory holds the implementation, a `pytest` test file, and a README covering the
problem statement and the key invariants / non-obvious decisions.

## Running the tests

```sh
uv sync --group dev && uv run pytest      # or: pip install pytest && pytest
```

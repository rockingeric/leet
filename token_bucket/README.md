# Token Bucket Rate Limiter

**Problem.** Allow up to `capacity` tokens, refilling `refill_rate` tokens every
`refill_period` seconds. `consume(n)` is all-or-nothing: grant `n` and return `True`,
or grant nothing and return `False`. Must be safe under concurrent callers.

**Design.** Lazy refill: instead of a background timer, each `consume` computes how
many whole refill periods have elapsed since `last_refill` and tops up accordingly.

## Invariants
- **Capacity ceiling** — refill is clamped by `empty_spots`; tokens never exceed `capacity`,
  no matter how long the bucket sat idle.
- **All-or-nothing** — a denied request spends nothing; the token count is untouched on `False`.
- **No token loss on partial periods** — `divmod` splits elapsed time into whole periods
  plus a remainder, and `last_refill` advances only by the consumed whole periods
  (`current_time - rest`), so fractional time carries forward instead of being discarded.

## Non-obvious decisions
- **The lock is correct by design, not by luck.** `tokens -= n` is a read-modify-write;
  under contention two threads could both read the same count and each decrement it,
  over-granting past capacity. The `threading.Lock` serializes the whole
  refill-and-consume section so that can't happen.
- **Why the test can actually catch a missing lock.** The GIL often *masks* this race —
  the interpreter rarely switches mid-`-=` — so a naive test passes even with no lock.
  `consume` therefore includes a tiny `sleep` inside the critical section to widen the
  window, and `test_thread_safe` fires 100 barrier-synchronized threads at a 50-token
  bucket and asserts **exactly 50** grants. Remove the lock and it fails. Correctness
  must not depend on the GIL.

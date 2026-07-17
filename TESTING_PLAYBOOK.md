# Testing Checklist

## Quick scan

1. Name the rule that must never break. If you can't, you can't test it.
2. Test the edges: empty, one, many, at the limit, one over, duplicate, out of order, at the same time.
3. For threads: make them clash with a barrier, check a rule a race would break, and confirm it fails without the lock.
4. Fake the clock. Check the delays and the run count, never wait on real time.
5. Test the risky, complex, high-impact code. Skip trivial glue.
6. Test what the code does, not how it's built. Refactors shouldn't break tests.
7. Match effort to risk, and know when to stop.
8. When a test fails, find out if the test or the code is wrong. Flaky is a clue, not noise.
9. Keep every test independent: no order, clock, network, or shared state.

---

## Same list, explained

### 1. Name the rule
What must *always* be true, no matter the input or timing?
A limit never passed, a thing never owned by two callers, speed still holds, order and state still right.
Can't name it means you don't know it well enough to test it.

### 2. Check the edges (bugs hide here, not in the middle)
empty, one, many, **right at the limit** (off-by-one), **one over** (the reject path), duplicate, out of order, at the same time.

### 3. Threads: do all three or the test is fake
1. **Make them clash.** Use `threading.Barrier(N)`, not a spawn loop (spawned threads start one by one, so the bug hides).
2. **Check a rule a race would break.** A count, a set size, a duplicate. "It didn't crash" proves nothing.
3. **Watch it fail without the lock.** Take the lock out, run 5 to 10 times, see it break. A race test you've never seen fail? You don't know if it works.

*Careful:* passing doesn't mean safe. Locks are right because you designed them right, not because the test passed. Won't break? Push harder: more threads, a barrier, or `sleep(0)` between the check and the change. This bites for real in free-threaded Python (3.13+).

### 4. Timing: fake the clock, don't wait
Swap `time.sleep` or the clock for a spy, then check the delays and how many times it ran. Never check real elapsed time (slow and flaky).

### 5. Test the right things
Spend effort where it matters: risky, complex, or high-blast-radius code. Don't write brittle tests for trivial glue. Knowing what *not* to test is half the skill. A suite full of low-value tests is a cost, not a safety net.

### 6. Test behavior, not how it's built
Test what the code *does*, not how it does it inside. If a clean refactor turns the suite red even though behavior is unchanged, the tests were tied to the wrong thing. Good tests break only when real behavior breaks.

### 7. Match effort to risk
How much testing is enough depends on the code. A payment path gets heavy rigor; a log formatter doesn't. Judge the cost of being wrong, and know when you've done enough and can stop.

### 8. Read failures well
When a test fails, figure out whether the *test* is wrong or the *code* is. A flaky test is a clue, often a real race (see the note above), not just noise to retry away. Don't paper over it.

### 9. Keep tests independent
A test shouldn't depend on run order, the real clock, the network, or the state left by another test. Deterministic, isolated tests are the difference between a suite you trust and one you learn to ignore.
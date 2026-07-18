# Connection Pool

**Problem.** Manage a fixed set of reusable connections with safe checkout, timeout,
health checks, and clean shutdown.

**Design.** A condition variable guards two sets of state: available connections in a deque
and checked-out connections in a set. `acquire()` blocks until a healthy connection is
available, `release()` returns it, and `close()` flips the pool into shutdown mode.

## Workflow

```text
borrow() / acquire()
        |
        v
[condition lock]
        |
        v
available connection?
     /           \
    no           yes
    |              |
    v              v
wait / timeout   pop conn
    |              |
    v              v
pool closed?    healthy?
   /     \       /    \
  yes    no     no    yes
  |       |      |      |
  v       v      v      v
 raise  keep   replace  lease
 closed waiting   |
                  v
             checked_out
                  |
                  v
         with lease / release()
                  |
                  v
        return to deque or close on shutdown
```

## Invariants
- **No over-allocation** — checked-out connections never exceed pool size.
- **No double release** — the same connection cannot be returned twice.
- **Closed pool is final** — once closed, new acquires fail and released idle connections are closed.
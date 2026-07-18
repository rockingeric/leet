# Python Interview Prep

Tiered, spec-first Python practice with adversarial, invariant-based tests.

## Workflow Maps

Each project below has a text-art workflow that traces the public path through the code.

```text
LRU Cache

get(key) / put(key, value)
					|
					v
	 [hash map lookup]
			/        \
		 v          v
	hit?        miss?
	 |            |
	 v            v
 touch node   create node
 (move front)    |
	 |             v
	 +-------> [linked list front]
								 |
								 v
				if over capacity -> evict tail
```

```text
Token Bucket

consume(n)
		|
		v
[lock]
		|
		v
check elapsed time since last_refill
		|
		v
whole refill periods passed?
	 /      \
	no      yes
	|         |
	v         v
tokens     add clamped refill
unchanged     |
	|           v
	+-------> enough tokens?
							 /      \
							no      yes
							|         |
							v         v
						False    subtract n
												 |
												 v
											 True
```

```text
Retry Decorator

call wrapped function
				|
				v
	 success? ---------> return value
				|
				no
				v
 caught allowed error?
		 /          \
		no          yes
		|             |
		v             v
 re-raise     attempts left?
								 /      \
								no      yes
								|         |
								v         v
						 raise      sleep backoff
												 + jitter
													 |
													 v
										 call wrapped function
```

```text
Connection Pool

borrow()/acquire()
				|
				v
	 [condition]
				|
				v
 available connection?
		 /           \
		no           yes
		|              |
		v              v
 wait / timeout  pop conn
		|              |
		v              v
 pool closed?   healthy?
	 /     \        /    \
	yes    no      no    yes
	|       |       |      |
	v       v       v      v
	stop   keep   replace  lease
					waiting  |
									 v
							checked out
									 |
									 v
						with lease / release()
									 |
									 v
				 return conn or close on shutdown
```

**Tier 1 — Production primitives** (concurrency & systems, LLD / machine-coding style)
- [x] LRU cache
- [x] Token bucket rate limiter
- [x] Retry decorator
- [x] Connection pool

**Tier 2 — DSA** (classic algorithm screening)
- [ ] _coming soon_

**Tier 3 — System design**
- [ ] _coming soon_
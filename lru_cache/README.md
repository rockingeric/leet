# LRU Cache

**Problem.** Build a fixed-capacity cache with `O(1)` `get` and `put`. On overflow,
evict the least-recently-used key. Every `get`/`put` counts as a use.

**Design.** A hash map (`key -> node`) for `O(1)` lookup, backed by a doubly linked
list that orders nodes by recency (most-recent at the front, LRU at the tail).
Eviction is a tail unlink; a touch is an unlink-and-prepend. Both are `O(1)`
because the map hands us the node directly — no list scan.

## Invariants
- **Capacity is never exceeded** — `len(nodes) <= capacity` after every operation.
- **Map and list stay in sync** — one node per key, list length == map size.
- **Recency order is correct** — the tail is always the true LRU; it's what gets evicted.

## Non-obvious decisions
- **Self-caught fall-through bug.** In `put`, an existing key updates in place and
  **returns early**. Without that `return`, the code falls through to the eviction +
  insert path and creates a *second* node for the same key — a phantom the map no
  longer points at. `test_update_existing_key_no_duplicate_node` is the adversarial
  test that pins this: re-put a key, assert exactly one node in both the map and the list.
- **Miss returns `None` by fall-through**, not by raising — a deliberate cache-miss signal.

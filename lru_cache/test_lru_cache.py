from lru_cache import LRUCache


def _list_len(cache):
    n, cur = 0, cache.list.root
    while cur:
        n += 1
        cur = cur.next
    return n


def test_get_hit_and_miss():
    cache = LRUCache(2)
    cache.put("a", 1)
    assert cache.get("a") == 1
    assert cache.get("missing") is None


def test_capacity_never_exceeded():
    cache = LRUCache(2)
    for i in range(100):
        cache.put(i, i)
        assert len(cache.nodes) <= 2
        assert _list_len(cache) == len(cache.nodes)


def test_recency_order_evicts_lru():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1               # "a" is now most-recently used
    cache.put("c", 3)                        # must evict "b", the LRU
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_update_existing_key_no_duplicate_node():
    cache = LRUCache(2)
    cache.put("k", 1)
    cache.put("k", 2)
    assert cache.get("k") == 2
    assert len(cache.nodes) == 1
    assert _list_len(cache) == 1

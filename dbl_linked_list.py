class Node:
    def __init__(self, key, data):
        self.key = key
        self.data = data
        self.prev = None
        self.next = None


class DoublyLinkedList:
    def __init__(self):
        self.root = None
        self.tail = None

    def append(self, node):
        if self.root is None:
            self.root = node
        else:
            node.prev = self.tail
            self.tail.next = node

        self.tail = node

    def prepend(self, node):
        if self.root is None:
            self.root = self.tail = node
        else:
            node.next = self.root
            self.root.prev = node
            self.root = node

    def delete(self, node):
        if node.prev is not None:
            node.prev.next = node.next
        else:
            self.root = node.next

        if node.next is not None:
            node.next.prev = node.prev
        else:
            self.tail = node.prev

        node.prev = node.next = None

    def show(self):
        cur = self.root
        while cur: 
            print(cur.data)
            cur = cur.next

    def keys_front_to_back(self):
        cur = self.root
        results = []
        while cur:
            results.append(cur.data)
            cur = cur.next

        return results

    def get(self, node):
        self.delete(node)
        self.prepend(node)

        return node


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.nodes = {}
        self.list = DoublyLinkedList()

    def get(self, key):
        if key in self.nodes:
            return self.list.get(self.nodes[key]).data

    def put(self, key, value):
        if key in self.nodes:
            node = self.nodes[key]
            node.data = value
            self.list.get(node)
            return

        if len(self.nodes) >= self.capacity:
            lru = self.list.tail
            self.list.delete(lru)
            del self.nodes[lru.key]

        node = Node(key, value)
        self.nodes[key] = node
        self.list.prepend(node)


def demo():
    cache = LRUCache(2)

    cache.put('user_name', 'e.martins')

    assert cache.get('user_name') == 'e.martins'

    cache.put('name', 'Eric')
    cache.put('dob', '30/11/1992')

    assert cache.get('user_name') is None

    print('OK')


if __name__ == "__main__":
    demo()

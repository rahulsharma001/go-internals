package lru_cache

import (
	"container/list"
	"sync"
)

// Cache owns both the index and recency list. The list front is most recent,
// and every map entry points to exactly one list element.
type Cache[K comparable, V any] struct {
	mu       sync.Mutex
	capacity int
	order    *list.List
	byKey    map[K]*list.Element
}

func New[K comparable, V any](capacity int) (*Cache[K, V], error) {
	if capacity <= 0 {
		return nil, ErrInvalidCapacity
	}
	return &Cache[K, V]{
		capacity: capacity,
		order:    list.New(),
		byKey:    make(map[K]*list.Element, capacity),
	}, nil
}

func (c *Cache[K, V]) Get(key K) (V, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	var zero V
	element, ok := c.byKey[key]
	if !ok {
		return zero, false
	}
	c.order.MoveToFront(element)
	return element.Value.(pair[K, V]).value, true
}

func (c *Cache[K, V]) Put(key K, value V) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if element, ok := c.byKey[key]; ok {
		element.Value = pair[K, V]{key: key, value: value}
		c.order.MoveToFront(element)
		return
	}
	element := c.order.PushFront(pair[K, V]{key: key, value: value})
	c.byKey[key] = element
	if c.order.Len() <= c.capacity {
		return
	}
	victim := c.order.Back()
	item := victim.Value.(pair[K, V])
	delete(c.byKey, item.key)
	c.order.Remove(victim)
}

func (c *Cache[K, V]) Len() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.order.Len()
}

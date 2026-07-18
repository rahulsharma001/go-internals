package ttl_cache

import (
	"sync"
	"time"
)

// Cache uses lazy expiration: operations remove expired entries, so no cleanup
// goroutine or shutdown lifecycle is required. The cache owns entries, and no
// callback runs under its lock.
type Cache[K comparable, V any] struct {
	mu      sync.Mutex
	clock   Clock
	entries map[K]entry[V]
}

func New[K comparable, V any]() *Cache[K, V] {
	return NewWithClock[K, V](systemClock{})
}

func NewWithClock[K comparable, V any](clock Clock) *Cache[K, V] {
	if clock == nil {
		clock = systemClock{}
	}
	return &Cache[K, V]{clock: clock, entries: make(map[K]entry[V])}
}

func (c *Cache[K, V]) Set(key K, value V, ttl time.Duration) error {
	if ttl <= 0 {
		return ErrInvalidTTL
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	c.entries[key] = entry[V]{value: value, expiresAt: c.clock.Now().Add(ttl)}
	return nil
}

func (c *Cache[K, V]) Get(key K) (V, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	var zero V
	item, ok := c.entries[key]
	if !ok {
		return zero, false
	}
	if !c.clock.Now().Before(item.expiresAt) {
		delete(c.entries, key)
		return zero, false
	}
	return item.value, true
}

func (c *Cache[K, V]) Delete(key K) bool {
	c.mu.Lock()
	defer c.mu.Unlock()
	if _, ok := c.entries[key]; !ok {
		return false
	}
	delete(c.entries, key)
	return true
}

func (c *Cache[K, V]) Len() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	now := c.clock.Now()
	for key, item := range c.entries {
		if !now.Before(item.expiresAt) {
			delete(c.entries, key)
		}
	}
	return len(c.entries)
}

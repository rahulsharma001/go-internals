package ttl_cache

import (
	"sync"
	"testing"
	"time"
)

type fakeClock struct {
	mu  sync.Mutex
	now time.Time
}

func (c *fakeClock) Now() time.Time {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.now
}

func (c *fakeClock) Advance(d time.Duration) {
	c.mu.Lock()
	c.now = c.now.Add(d)
	c.mu.Unlock()
}

func TestCacheExpiresAtBoundary(t *testing.T) {
	clock := &fakeClock{now: time.Unix(0, 0)}
	cache := NewWithClock[string, int](clock)
	if err := cache.Set("a", 7, time.Minute); err != nil {
		t.Fatal(err)
	}
	if value, ok := cache.Get("a"); !ok || value != 7 {
		t.Fatalf("Get() = %v, %v; want 7, true", value, ok)
	}
	clock.Advance(time.Minute)
	if _, ok := cache.Get("a"); ok {
		t.Fatal("expired key was returned")
	}
	if got := cache.Len(); got != 0 {
		t.Fatalf("Len() = %d; want 0", got)
	}
}

func TestCacheConcurrentSetGet(t *testing.T) {
	cache := New[int, int]()
	var wg sync.WaitGroup
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func(value int) {
			defer wg.Done()
			if err := cache.Set(value, value, time.Minute); err != nil {
				t.Errorf("Set() error = %v", err)
				return
			}
			if got, ok := cache.Get(value); !ok || got != value {
				t.Errorf("Get(%d) = %d, %v", value, got, ok)
			}
		}(i)
	}
	wg.Wait()
}

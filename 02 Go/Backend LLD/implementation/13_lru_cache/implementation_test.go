package lru_cache

import (
	"sync"
	"testing"
)

func TestCacheEvictsLeastRecentlyUsed(t *testing.T) {
	cache, err := New[string, int](2)
	if err != nil {
		t.Fatal(err)
	}
	cache.Put("a", 1)
	cache.Put("b", 2)
	if _, ok := cache.Get("a"); !ok {
		t.Fatal("a should exist")
	}
	cache.Put("c", 3)
	if _, ok := cache.Get("b"); ok {
		t.Fatal("b should have been evicted")
	}
	if value, ok := cache.Get("c"); !ok || value != 3 {
		t.Fatalf("Get(c) = %d, %v", value, ok)
	}
}

func TestCacheUpdateDoesNotGrow(t *testing.T) {
	cache, _ := New[string, int](1)
	cache.Put("a", 1)
	cache.Put("a", 2)
	if got := cache.Len(); got != 1 {
		t.Fatalf("Len() = %d; want 1", got)
	}
	if value, _ := cache.Get("a"); value != 2 {
		t.Fatalf("Get(a) = %d; want 2", value)
	}
}

func TestCacheConcurrentAccess(t *testing.T) {
	cache, _ := New[int, int](8)
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(value int) {
			defer wg.Done()
			cache.Put(value%16, value)
			cache.Get(value % 16)
		}(i)
	}
	wg.Wait()
	if cache.Len() > 8 {
		t.Fatalf("Len() = %d; exceeds capacity", cache.Len())
	}
}

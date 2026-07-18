package token_bucket_rate_limiter

import (
	"context"
	"errors"
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

func TestLimiterBurstAndRefill(t *testing.T) {
	clock := &fakeClock{now: time.Unix(0, 0)}
	limiter, err := NewWithClock(2, 3, clock)
	if err != nil {
		t.Fatal(err)
	}
	if !limiter.AllowN(3) {
		t.Fatal("initial burst should be available")
	}
	if limiter.AllowN(1) {
		t.Fatal("empty bucket allowed a token")
	}
	clock.Advance(500 * time.Millisecond)
	if !limiter.AllowN(1) {
		t.Fatal("one token should refill")
	}
}

func TestLimiterWaitHonorsCancellation(t *testing.T) {
	limiter, _ := New(1, 1)
	if !limiter.AllowN(1) {
		t.Fatal("initial token unavailable")
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if err := limiter.WaitN(ctx, 1); !errors.Is(err, context.Canceled) {
		t.Fatalf("WaitN() error = %v; want context.Canceled", err)
	}
}

func TestLimiterConcurrentAllowanceNeverExceedsBurst(t *testing.T) {
	clock := &fakeClock{now: time.Unix(0, 0)}
	limiter, _ := NewWithClock(1, 10, clock)
	var allowed int
	var mu sync.Mutex
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if limiter.AllowN(1) {
				mu.Lock()
				allowed++
				mu.Unlock()
			}
		}()
	}
	wg.Wait()
	if allowed != 10 {
		t.Fatalf("allowed %d calls; want 10", allowed)
	}
}

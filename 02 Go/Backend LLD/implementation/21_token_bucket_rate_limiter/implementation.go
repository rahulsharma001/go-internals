package token_bucket_rate_limiter

import (
	"context"
	"sync"
	"time"
)

// Limiter refills continuously at rate tokens/second up to burst. It owns all
// mutable state and has no goroutine or shutdown lifecycle.
type Limiter struct {
	mu     sync.Mutex
	clock  Clock
	rate   float64
	burst  float64
	tokens float64
	last   time.Time
}

func New(rate float64, burst int) (*Limiter, error) {
	return NewWithClock(rate, burst, systemClock{})
}

func NewWithClock(rate float64, burst int, clock Clock) (*Limiter, error) {
	if rate <= 0 || burst <= 0 {
		return nil, ErrInvalidConfig
	}
	if clock == nil {
		clock = systemClock{}
	}
	now := clock.Now()
	return &Limiter{clock: clock, rate: rate, burst: float64(burst), tokens: float64(burst), last: now}, nil
}

func (l *Limiter) refillLocked(now time.Time) {
	if now.Before(l.last) {
		l.last = now
		return
	}
	l.tokens += now.Sub(l.last).Seconds() * l.rate
	if l.tokens > l.burst {
		l.tokens = l.burst
	}
	l.last = now
}

func (l *Limiter) try(n int) (allowed bool, wait time.Duration) {
	if n <= 0 {
		return true, 0
	}
	l.mu.Lock()
	defer l.mu.Unlock()
	if float64(n) > l.burst {
		return false, -1
	}
	l.refillLocked(l.clock.Now())
	if l.tokens >= float64(n) {
		l.tokens -= float64(n)
		return true, 0
	}
	seconds := (float64(n) - l.tokens) / l.rate
	return false, time.Duration(seconds * float64(time.Second))
}

func (l *Limiter) AllowN(n int) bool {
	allowed, _ := l.try(n)
	return allowed
}

// WaitN waits without reserving future capacity. Competing callers may win the
// next tokens, so this API provides no strict fairness guarantee.
func (l *Limiter) WaitN(ctx context.Context, n int) error {
	for {
		allowed, wait := l.try(n)
		if allowed {
			return nil
		}
		if wait < 0 {
			return ErrInvalidConfig
		}
		if wait <= 0 {
			wait = time.Nanosecond
		}
		timer := time.NewTimer(wait)
		select {
		case <-ctx.Done():
			if !timer.Stop() {
				<-timer.C
			}
			return ctx.Err()
		case <-timer.C:
		}
	}
}

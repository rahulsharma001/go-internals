// Package token_bucket_rate_limiter implements a thread-safe token bucket.
package token_bucket_rate_limiter

import (
	"errors"
	"time"
)

var ErrInvalidConfig = errors.New("rate and burst must be positive")

type Clock interface {
	Now() time.Time
}

type systemClock struct{}

func (systemClock) Now() time.Time { return time.Now() }

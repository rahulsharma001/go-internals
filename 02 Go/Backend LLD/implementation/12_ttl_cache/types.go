// Package ttl_cache implements a thread-safe cache with lazy expiration.
package ttl_cache

import (
	"errors"
	"time"
)

var ErrInvalidTTL = errors.New("ttl must be positive")

type Clock interface {
	Now() time.Time
}

type systemClock struct{}

func (systemClock) Now() time.Time { return time.Now() }

type entry[V any] struct {
	value     V
	expiresAt time.Time
}

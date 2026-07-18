// Package lru_cache implements a thread-safe least-recently-used cache.
package lru_cache

import "errors"

var ErrInvalidCapacity = errors.New("capacity must be positive")

type pair[K comparable, V any] struct {
	key   K
	value V
}

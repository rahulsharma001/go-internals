// Package thread_safe_bounded_queue implements a bounded blocking FIFO.
package thread_safe_bounded_queue

import "errors"

var (
	ErrClosed          = errors.New("bounded queue is closed")
	ErrInvalidCapacity = errors.New("bounded queue capacity must be positive")
)

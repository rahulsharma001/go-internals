package thread_safe_bounded_queue

import (
	"context"
	"sync"
)

// Queue is a bounded FIFO. The Queue owns changed and is the only component
// that closes/replaces it. Closing drains accepted items before Dequeue returns
// ErrClosed.
type Queue[T any] struct {
	mu       sync.Mutex
	items    []T
	capacity int
	closed   bool
	changed  chan struct{}
}

func New[T any](capacity int) (*Queue[T], error) {
	if capacity <= 0 {
		return nil, ErrInvalidCapacity
	}
	return &Queue[T]{
		items:    make([]T, 0, capacity),
		capacity: capacity,
		changed:  make(chan struct{}),
	}, nil
}

// signalLocked wakes current waiters. q.mu must be held.
func (q *Queue[T]) signalLocked() {
	close(q.changed)
	q.changed = make(chan struct{})
}

func (q *Queue[T]) Enqueue(ctx context.Context, value T) error {
	for {
		q.mu.Lock()
		if q.closed {
			q.mu.Unlock()
			return ErrClosed
		}
		if len(q.items) < q.capacity {
			q.items = append(q.items, value)
			q.signalLocked()
			q.mu.Unlock()
			return nil
		}
		changed := q.changed
		q.mu.Unlock()

		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-changed:
		}
	}
}

func (q *Queue[T]) Dequeue(ctx context.Context) (T, error) {
	var zero T
	for {
		q.mu.Lock()
		if len(q.items) > 0 {
			value := q.items[0]
			q.items[0] = zero
			q.items = q.items[1:]
			q.signalLocked()
			q.mu.Unlock()
			return value, nil
		}
		if q.closed {
			q.mu.Unlock()
			return zero, ErrClosed
		}
		changed := q.changed
		q.mu.Unlock()

		select {
		case <-ctx.Done():
			return zero, ctx.Err()
		case <-changed:
		}
	}
}

// Close rejects future enqueue operations and wakes all waiters. It is
// idempotent; already accepted items remain available to Dequeue.
func (q *Queue[T]) Close() {
	q.mu.Lock()
	defer q.mu.Unlock()
	if q.closed {
		return
	}
	q.closed = true
	q.signalLocked()
}

func (q *Queue[T]) Len() int {
	q.mu.Lock()
	defer q.mu.Unlock()
	return len(q.items)
}

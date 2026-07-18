// Package worker_pool implements a fixed-size, bounded worker pool.
package worker_pool

import (
	"context"
	"errors"
)

var (
	ErrClosed        = errors.New("worker pool is closed")
	ErrInvalidConfig = errors.New("workers must be positive and queue size non-negative")
)

type Job func(context.Context) error

type task struct {
	ctx context.Context
	job Job
}

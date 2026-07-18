package worker_pool

import (
	"context"
	"sync"
)

// Pool owns jobs and is the only component that closes it. Close drains all
// accepted jobs. Job callbacks never execute while a pool lock is held.
type Pool struct {
	mu        sync.RWMutex
	jobs      chan task
	workers   sync.WaitGroup
	closeOnce sync.Once
	done      chan struct{}
	closed    bool
}

func New(workers, queueSize int) (*Pool, error) {
	if workers <= 0 || queueSize < 0 {
		return nil, ErrInvalidConfig
	}
	p := &Pool{
		jobs: make(chan task, queueSize),
		done: make(chan struct{}),
	}
	p.workers.Add(workers)
	for i := 0; i < workers; i++ {
		go p.run()
	}
	return p, nil
}

func (p *Pool) run() {
	defer p.workers.Done()
	for task := range p.jobs {
		if task.ctx.Err() == nil {
			_ = task.job(task.ctx)
		}
	}
}

// Submit blocks under backpressure until accepted, the context ends, or the
// pool closes. The read lock prevents a send racing with channel closure.
func (p *Pool) Submit(ctx context.Context, job Job) error {
	if job == nil {
		return ErrInvalidConfig
	}
	p.mu.RLock()
	defer p.mu.RUnlock()
	if p.closed {
		return ErrClosed
	}
	select {
	case p.jobs <- task{ctx: ctx, job: job}:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

// Close stops admission, closes the producer-owned jobs channel, drains
// accepted work, and waits for owned workers. The wait respects ctx, while
// shutdown continues in the background if the caller's deadline expires.
func (p *Pool) Close(ctx context.Context) error {
	p.closeOnce.Do(func() {
		p.mu.Lock()
		p.closed = true
		close(p.jobs)
		p.mu.Unlock()
		go func() {
			p.workers.Wait()
			close(p.done)
		}()
	})

	select {
	case <-p.done:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

package worker_pool

import (
	"context"
	"errors"
	"sync/atomic"
	"testing"
	"time"
)

func TestPoolRunsAcceptedJobsAndCloses(t *testing.T) {
	p, err := New(3, 4)
	if err != nil {
		t.Fatal(err)
	}
	var ran atomic.Int32
	for i := 0; i < 20; i++ {
		if err := p.Submit(context.Background(), func(context.Context) error {
			ran.Add(1)
			return nil
		}); err != nil {
			t.Fatal(err)
		}
	}
	if err := p.Close(context.Background()); err != nil {
		t.Fatal(err)
	}
	if got := ran.Load(); got != 20 {
		t.Fatalf("ran %d jobs; want 20", got)
	}
	if err := p.Submit(context.Background(), func(context.Context) error { return nil }); !errors.Is(err, ErrClosed) {
		t.Fatalf("Submit() error = %v; want ErrClosed", err)
	}
}

func TestPoolBackpressureHonorsCancellation(t *testing.T) {
	p, _ := New(1, 0)
	started := make(chan struct{})
	release := make(chan struct{})
	if err := p.Submit(context.Background(), func(context.Context) error {
		close(started)
		<-release
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	<-started

	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if err := p.Submit(ctx, func(context.Context) error { return nil }); !errors.Is(err, context.Canceled) {
		t.Fatalf("Submit() error = %v; want context.Canceled", err)
	}
	close(release)
	if err := p.Close(context.Background()); err != nil {
		t.Fatal(err)
	}
}

func TestPoolCloseDeadlineDoesNotAbandonShutdown(t *testing.T) {
	p, _ := New(1, 0)
	release := make(chan struct{})
	if err := p.Submit(context.Background(), func(context.Context) error {
		<-release
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancel()
	if err := p.Close(ctx); !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("Close() error = %v; want deadline exceeded", err)
	}
	close(release)
	if err := p.Close(context.Background()); err != nil {
		t.Fatal(err)
	}
}

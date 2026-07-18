package thread_safe_bounded_queue

import (
	"context"
	"errors"
	"sync"
	"testing"
	"time"
)

func TestQueueFIFOAndDrainAfterClose(t *testing.T) {
	q, err := New[int](2)
	if err != nil {
		t.Fatal(err)
	}
	if err := q.Enqueue(context.Background(), 10); err != nil {
		t.Fatal(err)
	}
	if err := q.Enqueue(context.Background(), 20); err != nil {
		t.Fatal(err)
	}
	q.Close()
	for _, want := range []int{10, 20} {
		got, err := q.Dequeue(context.Background())
		if err != nil || got != want {
			t.Fatalf("Dequeue() = %v, %v; want %v, nil", got, err, want)
		}
	}
	if _, err := q.Dequeue(context.Background()); !errors.Is(err, ErrClosed) {
		t.Fatalf("Dequeue() error = %v; want ErrClosed", err)
	}
}

func TestQueueBlockedEnqueueCanBeCancelled(t *testing.T) {
	q, _ := New[int](1)
	if err := q.Enqueue(context.Background(), 1); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if err := q.Enqueue(ctx, 2); !errors.Is(err, context.Canceled) {
		t.Fatalf("Enqueue() error = %v; want context.Canceled", err)
	}
}

func TestQueueConcurrentProducersAndConsumer(t *testing.T) {
	q, _ := New[int](4)
	const count = 100
	var producers sync.WaitGroup
	for producer := 0; producer < 2; producer++ {
		producers.Add(1)
		go func(offset int) {
			defer producers.Done()
			for i := 0; i < count/2; i++ {
				if err := q.Enqueue(context.Background(), offset+i); err != nil {
					t.Errorf("Enqueue() error = %v", err)
					return
				}
			}
		}(producer * count)
	}

	values := make(chan int, count)
	go func() {
		for {
			value, err := q.Dequeue(context.Background())
			if errors.Is(err, ErrClosed) {
				close(values)
				return
			}
			if err != nil {
				t.Errorf("Dequeue() error = %v", err)
				close(values)
				return
			}
			values <- value
		}
	}()
	producers.Wait()
	q.Close()

	received := 0
	for range values {
		received++
	}
	if received != count {
		t.Fatalf("received %d values; want %d", received, count)
	}
}

func TestQueueDequeueDeadline(t *testing.T) {
	q, _ := New[int](1)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancel()
	if _, err := q.Dequeue(ctx); !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("Dequeue() error = %v; want deadline exceeded", err)
	}
}

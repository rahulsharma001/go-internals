# 25. Bulkhead Executor

Prompt-first Go package for [[Bulkhead Executor]]. The initial files intentionally compile without claiming implementation evidence. Add behavior only during a timed attempt, then record tests and review dates in the tracker.

Package: bulkhead_executor  
Verify: go test ./...  
Concurrent package: yes; also run go test -race ./...

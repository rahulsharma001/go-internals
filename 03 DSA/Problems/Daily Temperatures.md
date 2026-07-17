---
type: problem
domain: dsa
status: reference-not-attempted
pattern: stack-queue
source_conversations:
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Daily Temperatures

LeetCode: https://leetcode.com/problems/daily-temperatures/

## Problem summary

For each day, return how many days pass before a strictly warmer temperature; return zero if none exists.

## Pattern

[[Stack and Queue Pattern]] — decreasing stack of unresolved indices.

## Brute-force intuition

For every day scan forward for the first warmer day: `O(n²)` time.

## Optimal intuition

Indices on the stack have not yet found a warmer day and their temperatures are decreasing. A warmer current day resolves and pops every colder stack top.

## Dry run

`[73,74,75,71,69,72]`: day 1 resolves day 0; day 2 resolves day 1; day 5 resolves days 4 and 3. Day 2 remains unresolved in this prefix.

## Complete Go solution

```go
package main

import "fmt"

func dailyTemperatures(temperatures []int) []int {
	answer := make([]int, len(temperatures))
	stack := []int{}
	for i, temperature := range temperatures {
		for len(stack) > 0 && temperature > temperatures[stack[len(stack)-1]] {
			previous := stack[len(stack)-1]
			stack = stack[:len(stack)-1]
			answer[previous] = i - previous
		}
		stack = append(stack, i)
	}
	return answer
}

func main() {
	fmt.Println(dailyTemperatures([]int{73, 74, 75, 71, 69, 72, 76, 73}))
	fmt.Println(dailyTemperatures([]int{30, 29, 28}))
	fmt.Println(dailyTemperatures(nil))
}
```

Run: `go run main.go`.

## Complexity

`O(n)` time—each index is pushed and popped at most once—and `O(n)` space.

## Edge cases

Empty; one day; strictly decreasing; equal temperatures do not resolve each other; final unresolved days stay zero.

## Blank-editor success criteria

Finish in 30 minutes, explain amortized `O(n)`, compile decreasing/equal cases, then return the next-warmer index rather than the distance.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.

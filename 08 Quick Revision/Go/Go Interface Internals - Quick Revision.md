---
type: quick-revision
domain: go
topic: interface-internals
canonical: "[[Go Interface Internals]]"
---

# Go Interface Internals - Quick Revision

## 30-second definition and mental model

An interface value has a dynamic type and dynamic value. It is nil only when both are absent. A nil pointer stored inside an interface therefore produces a non-nil interface.

Five facts: method sets determine satisfaction; two-result assertions avoid panic; type switches handle alternatives; interface equality can panic for uncomparable dynamic values; runtime table names are implementation detail.

Common trap: returning `(*MyError)(nil)` as `error`.

Production example: return literal nil on success and use `errors.Is/As` across wrapped error boundaries.

Interview answer: “I explain typed nil from dynamic type/value first; runtime tables are a deeper, version-sensitive follow-up.”

Active recall: predict `err == nil` and repair the constructor.

Canonical: [[Go Interface Internals]] · Foundation: [[Go Interfaces]]

Index: [[Quick Revision Index]]

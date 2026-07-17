---
type: quick-revision
domain: system-design
review_time: 4-minutes
---
# Trade-off Vocabulary

Use decision language, not generic pros/cons:

- “I am optimizing for ___ under the stated ___ constraint.”
- “The strict invariant is ___; therefore I keep write authority in ___.”
- “I accept bounded staleness of ___ because ___ is not on the commit path.”
- “This reduces tail latency but increases ___ and introduces failure mode ___.”
- “The alternative is viable when ___ becomes more important than ___.”
- “This component is derived and rebuildable; the recovery cost is ___.”
- “At-least-once delivery means the effect requires idempotency/reconciliation at ___.”
- “Single-region writes simplify ___ but cost ___ during region failure.”
- “Precomputation shifts cost from read to write and fails under skew from ___.”
- “I would validate this choice with metric/experiment ___.”

Always name: decision, selected option, alternative, reason, weakness, reversal condition. See [[Trade-off Communication]].

# Engineering OS operating rules

## Mission

This Obsidian vault is an Engineering Operating System for becoming a
strong Senior/Staff Backend Engineer and preparing for Google-level interviews.

The vault must optimize:
- retrieval
- implementation
- active recall
- interview performance
- production decision-making

It must not become an encyclopedia or passive content dump.

## Safety

- Preserve existing information.
- Never permanently delete notes.
- Move obsolete or superseded originals to `99 Archive`.
- Never invent project details, production experience, metrics, scale, interview history, or personal achievements.
- Work incrementally by category.
- Do not perform large cross-vault changes without first creating an audit plan.
- Prefer improving an existing canonical note over creating a duplicate.
- Keep source traceability when content comes from imported conversations or articles.
- Never import credentials into permanent notes; redact them before creating or updating notes.
- Never commit raw ChatGPT exports or extracted source conversations.
- Run `tools/security/scan-secrets.sh` before every commit.
- Never bypass GitHub push protection or use an allow-secret URL.

## Canonical-note rule

Each technical concept should have one canonical note.

Examples:
- one Go Interfaces note
- one Worker Pool note
- one Kafka Consumer Groups note
- one Database Indexes note
- one Outbox Pattern note

Related notes should link to the canonical note instead of repeating the same explanation.

## Learning lifecycle

Important topics must support:

Learn
→ Implement
→ Explain
→ Revise
→ Interview
→ Record mistakes
→ Re-test

A topic is not complete merely because a note exists.

For implementation topics, active evidence must include a prompt-first
blank-editor drill, a complete executable invocation, an attempt record, and a
scheduled re-test. Record actual mistakes and their corrections; never infer a
personal mistake merely from generic teaching material.

## Current implementation priorities

Prioritize these before advanced internals:

1. Go slices
2. Go maps
3. Struct creation
4. Methods and receivers
5. Interfaces
6. Embedding and composition
7. Complete `main()` invocation
8. Error handling
9. Writing DSA solutions in Go
10. Modifying solutions under interview pressure

## Technical-note quality

Canonical notes should normally be concise but complete.

They should contain where relevant:
- problem being solved
- mental model
- essential concepts
- minimum executable example
- complete `main()` usage
- dry run
- production use
- success path
- failure path
- trade-offs
- common mistakes
- interview questions
- active-recall drill
- related notes

Quick-revision notes must be readable in under five minutes.

Every Go example intended to teach implementation must be executable and show
the complete `main()` invocation (or a complete test when that is the natural
entry point). Prefer improving the existing canonical, revision, or drill note
over creating another explanation of the same concept.

## System-design standard

System-design notes should use:

1. Requirements
2. Scale assumptions
3. Core entities
4. API design
5. Data model
6. High-level architecture
7. Complete success flow
8. Complete failure flow
9. Scaling bottlenecks
10. Reliability and observability
11. Security
12. Trade-offs
13. Real technology choices
14. Interview follow-ups
15. Five-minute revision

Reusable patterns should be linked rather than repeatedly copied.

## Personal-content boundary

Do not import unrelated health, shopping, travel, personal-finance,
household, social-media, or medical conversations into this engineering vault.

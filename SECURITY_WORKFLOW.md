# Repository Secret-Safety Workflow

## Boundary

Raw ChatGPT exports, extracted source conversations, and importer caches remain local inputs. They are ignored and must never be staged. Permanent engineering notes may retain useful technical explanations only after every credential and credentialed connection string is redacted.

Never bypass GitHub push protection. An alert means the credential is compromised: rotate or revoke it, remove it from the working tree and every Git ref, verify again, and only then push rewritten history with `--force-with-lease`.

## Before every commit

Run:

```bash
tools/security/scan-secrets.sh --staged
```

The scanner checks staged text without printing complete values. It blocks high-confidence AWS, GitHub, API, Slack, private-key, password/secret assignment, credentialed database URL, and signed bearer/JWT patterns. Clearly labelled redaction placeholders and standard fake examples are ignored.

For a broader local audit, including ignored local inputs, run:

```bash
tools/security/scan-secrets.sh --worktree
```

## Repository-local hook

Enable the committed hook once per clone:

```bash
git config core.hooksPath .githooks
```

The hook invokes the staged scanner and returns a non-zero status when a finding exists. No global Git or system configuration is required.

## Safe redaction

Use unambiguous placeholders such as:

- `[REDACTED_AWS_ACCESS_KEY_ID]`
- `[REDACTED_AWS_SECRET_ACCESS_KEY]`
- `[REDACTED_PASSWORD]`
- `[REDACTED_TOKEN]`
- `postgresql://[REDACTED_CREDENTIALS]@db.example.invalid/app`

Do not copy a real value into a remediation report, commit message, shell command, test fixture, or replacement file. Reports may include only a masked identifier, affected path and commit, and remediation status.

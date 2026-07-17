#!/usr/bin/env bash
set -uo pipefail

mode="${1:---staged}"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "secret scan: not inside a Git repository" >&2
  exit 2
}

scan_tmp="$(mktemp -d "${TMPDIR:-/tmp}/engineering-os-secret-scan.XXXXXX")" || exit 2
chmod 700 "$scan_tmp"
trap 'rm -rf -- "$scan_tmp"' EXIT HUP INT TERM

findings=0

scan_file() {
  local display_path="$1"
  local input_path="$2"

  # Bundled plugin programs contain scanner/test pattern strings, not vault credentials.
  if [[ "$display_path" == .obsidian/plugins/*/main.js || "$display_path" == tools/chatgpt_import/test_importer.py ]]; then
    return 0
  fi

  if ! LC_ALL=C grep -Iq . "$input_path" 2>/dev/null; then
    return 0
  fi

  local result
  result="$(perl - "$display_path" "$input_path" <<'PERL'
use strict;
use warnings;

my ($path, $file) = @ARGV;
open my $fh, '<', $file or exit 0;

sub approved_fake {
    my ($value) = @_;
    return 1 if !defined $value || $value eq '';
    return 1 if $value =~ /(?:REDACTED|EXAMPLE|DUMMY|FAKE|MOCK|CHANGEME|YOUR[_-]|PLACEHOLDER|\.\.\.)/i;
    return 1 if $value =~ /^<[^>]+>$/;
    return 1 if $value =~ /^\$/ || $value =~ /[()]/;
    return 0;
}

sub masked {
    my ($value) = @_;
    $value =~ s/^["']//;
    $value =~ s/["',;)]$//;
    return '[REDACTED]' if length($value) < 9;
    return substr($value, 0, 4) . ('*' x 12) . substr($value, -4);
}

sub emit_finding {
    my ($line_number, $type, $value) = @_;
    return if approved_fake($value);
    print "$path:$line_number: $type " . masked($value) . "\n";
}

my $line_number = 0;
while (my $line = <$fh>) {
    ++$line_number;

    while ($line =~ /\b((?:AKIA|ASIA|AIDA|AROA|AIPA|ANPA|ANVA|AGPA)[A-Z0-9]{16})\b/g) {
        emit_finding($line_number, 'AWS access-key ID', $1);
    }
    while ($line =~ /\b(github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b/g) {
        emit_finding($line_number, 'GitHub token', $1);
    }
    while ($line =~ /\b(sk-[A-Za-z0-9_-]{20,})\b/g) {
        emit_finding($line_number, 'API token', $1);
    }
    while ($line =~ /\b(xox[baprs]-[A-Za-z0-9-]{20,})\b/g) {
        emit_finding($line_number, 'Slack token', $1);
    }
    if ($line =~ /-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----/) {
        print "$path:$line_number: private-key material [REDACTED]\n";
    }
    while ($line =~ /\b(?:aws_secret_access_key|password|passwd|pwd|client_secret|oauth_client_secret|jwt_secret|signing_secret|api_key|access_token|refresh_token)\b\s*[:=]\s*["']?([^\s"'`,;}{]{8,})/ig) {
        emit_finding($line_number, 'credential assignment', $1);
    }
    while ($line =~ /\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis):\/\/([^\s\/@:]+):([^\s\/@]+)\@/ig) {
        emit_finding($line_number, 'credentialed connection string', "$1:$2");
    }
    while ($line =~ /\bBearer\s+([A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})\b/ig) {
        emit_finding($line_number, 'bearer/JWT token', $1);
    }

    if ($line =~ /\b(?:AKIA|ASIA|AIDA|AROA|AIPA|ANPA|ANVA|AGPA)[A-Z0-9]{16}\b/) {
        while ($line =~ /\b([A-Za-z0-9\/+]{40})\b/g) {
            emit_finding($line_number, 'AWS secret access key', $1);
        }
    }
}
PERL
)"

  if [[ -n "$result" ]]; then
    printf '%s\n' "$result" >&2
    findings=1
  fi
}

case "$mode" in
  --staged)
    while IFS= read -r -d '' path; do
      staged_file="$scan_tmp/staged"
      if git show ":$path" >"$staged_file" 2>/dev/null; then
        chmod 600 "$staged_file"
        scan_file "$path" "$staged_file"
      fi
    done < <(git -C "$repo_root" diff --cached --name-only --diff-filter=ACMR -z)
    ;;
  --worktree)
    while IFS= read -r -d '' path; do
      relative="${path#"$repo_root"/}"
      scan_file "$relative" "$path"
    done < <(find "$repo_root" -path "$repo_root/.git" -prune -o -type f -print0)
    ;;
  *)
    echo "usage: tools/security/scan-secrets.sh [--staged|--worktree]" >&2
    exit 2
    ;;
esac

if (( findings != 0 )); then
  echo "secret scan: blocked; redact the masked findings before committing" >&2
  exit 1
fi

echo "secret scan: passed ($mode)"

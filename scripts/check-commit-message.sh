#!/usr/bin/env bash
set -euo pipefail

message=${1:-}
if [[ -z "$message" ]]; then
  echo "usage: check-commit-message.sh 'type(scope): imperative summary'" >&2
  exit 2
fi

if [[ ! "$message" =~ ^(feat|fix|refactor|docs|test|ci|build|chore|perf|revert)(\([a-z0-9._/-]+\))?:[[:space:]][a-z].{2,}$ ]]; then
  echo "BLOCK: invalid Conventional Commit: $message" >&2
  echo "Use: type(scope): imperative summary" >&2
  exit 1
fi

if [[ ${#message} -gt 100 ]]; then
  echo "BLOCK: commit subject exceeds 100 characters" >&2
  exit 1
fi

echo "PASS: Conventional Commit"

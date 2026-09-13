#!/usr/bin/env bash
set -euo pipefail

fail=0
branch=$(git branch --show-current)
if [[ "$branch" == "main" || "$branch" == "master" ]]; then
  echo "BLOCK: work must happen on a topic branch (current: $branch)"
  fail=1
fi

if git diff --check; then :; else
  echo "BLOCK: whitespace errors found"
  fail=1
fi

if git diff --cached --name-only | grep -Eq '(^|/)(\.env|\.env\.local|.*\.pem|.*\.key)$'; then
  echo "BLOCK: sensitive-looking file staged"
  fail=1
fi

if git diff --cached | grep -nE '^\+.*(TODO|FIXME|debugger|console\.log\()' >/dev/null; then
  echo "WARN: debug/TODO text appears in staged additions"
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "INFO: working tree has changes; commit only files belonging to this task"
fi

if (( fail )); then exit 1; fi
echo "PASS: governance checks"

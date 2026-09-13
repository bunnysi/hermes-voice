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

# Public remotes: refuse live-looking keys in staged additions.
# Mark with `git config hermes.public true`. Private repos skip this.
# Household-domain checks stay in the skill (AI review), not this script —
# the script is copied into public repos and must not list private hosts.
if git config --get hermes.public 2>/dev/null | grep -qi '^true$'; then
  if git diff --cached | grep -E '^\+.*(ghp_[A-Za-z0-9]|github_pat_)' >/dev/null; then
    echo "BLOCK: public repo — live-looking keys in staged additions"
    fail=1
  fi
fi

if git diff --cached | grep -nE '^\+.*(TODO|FIXME|debugger|console\.log\()' >/dev/null; then
  echo "WARN: debug/TODO text appears in staged additions"
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "INFO: working tree has changes; commit only files belonging to this task"
fi

if (( fail )); then exit 1; fi
echo "PASS: governance checks"

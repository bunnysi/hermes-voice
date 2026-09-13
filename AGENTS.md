# AI Project Contract

This file is binding for AI coding agents working in this repository.

## Before editing

- Read this file, README, CONTRIBUTING, relevant docs, and `git status`/recent log.
- Confirm the task, acceptance criteria, target branch, and files in scope.
- Do not guess product facts, credentials, legal text, or release intent.
- Do not work directly on `main` unless the owner explicitly authorizes an emergency fix.

## During editing

- Make the smallest coherent change.
- Keep behavior, tests, docs, and user-facing copy consistent in one PR.
- Do not introduce unrelated cleanup, generated artifacts, secrets, debug code, or dependency churn.
- Follow the project's existing language, framework, formatting, and token conventions.
- Do not hardcode machine-local paths or live API keys.
- This repository is public: do not commit `.env`, live keys, or household/private domains (scan git history, not only HEAD).
- This plugin is a voice call, not a chat UI and not a tool-heavy agent loop.
- Do not add a Python LiveKit client, a second transport stack, or group chat.

## Before commit / push / merge

- Review the complete diff and scan for secrets, conflict markers, TODO/FIXME, debug output, and accidental files.
- Run `uv run ruff check .` and `uv run pytest`.
- New failures block the commit. Do not hide failures as warnings.
- Use a focused Conventional Commit: `type(scope): imperative summary`.
- Push a branch and use a PR. Do not bypass required checks.
- Update docs and `[Unreleased]` when behavior or user-facing output changes.
- Report exactly what was verified; never call an unverified change complete.

## Stop conditions

Stop and ask when scope, destructive action, public behavior, credentials, or factual copy is unclear. Block when security, correctness, required checks, or release prerequisites fail.

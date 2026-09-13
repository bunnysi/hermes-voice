# Development Workflow

## Branches

`main` is the protected integration branch. Work on `feat/*`, `fix/*`, `refactor/*`, `docs/*`, `test/*`, or `ci/*`.

## Local gate

Before opening a PR:

```bash
./scripts/governance-check.sh
uv sync --extra dev
uv run ruff check .
uv run pytest
```

`hermes plugins doctor . --ci` when Hermes is installed.

## PR gate

A PR must be focused, documented, tested where behavior changes, reviewed by the AI assistant, and green in CI.

## Commit gate

Use `type(scope): imperative summary`; one logical change per commit.

## Merge gate

Only merge after all required checks pass. Prefer squash merge into `main`. Delete the topic branch after merge.

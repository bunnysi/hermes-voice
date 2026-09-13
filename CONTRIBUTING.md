# Contributing

Thanks for contributing. This project uses a focused branch → PR → CI → merge workflow, including for solo development.

## Workflow

1. Start from an up-to-date `main`.
2. Create `feat/*`, `fix/*`, `refactor/*`, `docs/*`, `test/*`, or `ci/*`.
3. Keep one logical task per branch and PR.
4. Run local checks before pushing.
5. Open a PR using the template.
6. Merge only after AI review and required CI checks are green.
7. Prefer squash merge, then delete the branch.

## Commits

Use Conventional Commits:

```text
type(scope): imperative summary
```

Allowed types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `build`, `chore`, `perf`, `revert`.

Keep commits focused and reversible. Explain non-obvious or breaking changes in the body. Do not use `update`, `changes`, `misc`, or `final` as the only message.

## Required with behavior changes

- Tests added or updated.
- README/docs updated when behavior or usage changes.
- `CHANGELOG.md` updated under `[Unreleased]` for user-facing changes.
- No secrets, production credentials, or private infrastructure in the diff.

## Release

Only release from green `main`. Finalize the changelog, run the release checklist, create a `vMAJOR.MINOR.PATCH` tag, publish, and run a real smoke check. See `docs/release.md`.

## Security

Do not report vulnerabilities in public issues. Follow `SECURITY.md`.

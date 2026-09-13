# Release Workflow

```text
focused PR → CI green → merge to main → finalize CHANGELOG → tag → publish → smoke test
```

## Checklist

- [ ] `main` is up to date and clean
- [ ] Required CI is green
- [ ] `[Unreleased]` is complete
- [ ] Version follows `vMAJOR.MINOR.PATCH`
- [ ] Breaking changes are called out
- [ ] Tag points to the reviewed commit
- [ ] Published artifact is tested
- [ ] Rollback target is known

A build completing is not enough: install the plugin, run `hermes voice setup` against a throwaway config, and confirm `/api/session` does not return the Fish key.

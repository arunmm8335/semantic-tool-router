## Summary

<!-- What changed and why? Link the issue if one exists. -->

Fixes #

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Benchmark / evaluation change
- [ ] Documentation only
- [ ] Refactor (no behavior change)

## Test plan

- [ ] `python -m unittest discover -s tests`
- [ ] `ruff check src tests examples`
- [ ] `ruff format --check src tests examples`
- [ ] `mypy src/semantic_tool_router`

If retrieval behavior changed, include benchmark numbers:

```bash
python -m semantic_tool_router compare-retrievers --fixture-only \
  --markdown-output /tmp/comparison.md
```

| Metric | Before | After |
| --- | ---: | ---: |
| hit_rate@3 (live MCP) | | |
| top_1_accuracy (live MCP) | | |

## Changelog

- [ ] Updated `CHANGELOG.md` under **Unreleased**

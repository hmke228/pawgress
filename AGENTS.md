# Pawgress development conventions

## Scope and layout

- Use Python 3.13 and the existing team Project Plan. Pawgress is a CLI application.
- Code lives in `src/pawgress/`; direct unit tests in `tests/unit/` and subprocess
  integration tests in `tests/integration/`. `__main__.py` delegates to `cli.main`.
- AI, RAG, Behavioral Comparison, and Storage are placeholders. Storage will use
  SQLite through the standard-library `sqlite3` module.
- Do not implement Report Schema, AI integration, retrieval, comparison, database
  schemas, or storage logic without an explicit task authorizing that work.
- Requirements and architecture changes require approval. Keep dependencies minimal
  and Python configuration in `pyproject.toml`; hooks and CI use their YAML files.

## Setup and checks

Follow README's environment setup and activate `.venv`. From the repository root:

```sh
bash scripts/lint.sh
python -m pytest tests/unit
python -m pytest tests/integration --no-cov
pre-commit run --all-files
```

- Lint: `python -m ruff check .`; format check: `python -m ruff format --check .`.
- Apply formatting with `python -m ruff format .`; run both suites with
  `python -m pytest`. Unit coverage must exceed 90%; the configured minimum is 91%.
- Smoke-test `pawgress --help` and `python -m pawgress --help`.
- Pre-commit runs unit tests and coverage as well as lint/format checks. Its
  `--all-files` only includes tracked files; check new files with
  `pre-commit run --files <paths>` before staging. Keep Ruff hook/dependency pins aligned.

## Collaboration and style

- Never commit directly to `main`. Use separate `chore/`, `feat/`, or `fix/` branches
  and merge through reviewed PRs. Preserve existing work, CODEOWNERS, and settings.
- Keep each PR under 100 changed lines (additions plus deletions). Use `Refs #2`,
  `Refs #3`, or `Refs #4`; do not close issues before all requirements are complete.
- Keep #5 open for team requirements and MVP backlog finalization.
- Add tests with code changes; keep tests independent of network and external services.
- Use descriptive snake_case names, typed signatures, and Ruff formatting/import order.
- Never commit secrets, credentials, or generated data. Review and understand AI work;
  document or cite it when course policy requires.
- Do not commit, push, publish PRs, or change remote settings without user approval.

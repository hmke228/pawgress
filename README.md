# Pawgress

Pawgress is a Python CLI application for the CS 467 Capstone Project. The planned
application helps owners understand one target dog's observable behaviors and
compare observations over time. The existing team Project Plan defines the
product requirements and architecture.

This repository currently contains the development setup and a minimal CLI that
prints help. Report schemas, image analysis, retrieval, behavioral comparison,
and persistence are not implemented.

## Development setup

Prerequisites: Python 3.13, Git, and a POSIX shell (macOS, Linux, or WSL) for the
commands below. No API keys or database setup are needed.

```sh
git clone https://github.com/hmke228/pawgress.git
cd pawgress
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pre-commit install
```

Activate the virtual environment again in each new terminal. The editable
installation makes changes under `src/` available without reinstalling.
Dependencies and Python tool settings live in `pyproject.toml`.

## Run the CLI

```sh
pawgress --help
python -m pawgress --help
```

Both entry points also print help when called without arguments. There are no
application commands yet.

## Development checks

With the virtual environment active, run:

```sh
bash scripts/lint.sh
python -m pytest tests/unit
python -m pytest tests/integration --no-cov
pre-commit run --all-files
```

The lint script runs `python -m ruff check .` and
`python -m ruff format --check .`. To apply formatting:

```sh
python -m ruff format .
```

Pre-commit runs Ruff lint/format, whitespace/newline fixes, and the full unit
suite with a 91% minimum line coverage gate (greater than 90%). Formatting hooks
can change files; review those changes and rerun the checks. `--all-files` checks tracked files; newly created files
must be added to Git before that command includes them.

Ruff is pinned to the same version in `pyproject.toml` and
`.pre-commit-config.yaml`; update both together.

`python -m pytest` runs both suites. Unit coverage measures `src/pawgress`;
CI and pre-commit enforce the threshold using the unit suite independently.

## Continuous integration and setup issues

`.github/workflows/ci.yml` runs on all pull requests (including stacked PRs)
and pushes to `main`. The existing `CI Verification` workflow name and `verify`
job are kept.
CI installs Python 3.13 and the development dependencies with pip caching, then
runs lint/format checks, unit tests with the coverage gate, and integration tests.

- [Issue #2](https://github.com/hmke228/pawgress/issues/2): developer and agent docs.
- [Issue #3](https://github.com/hmke228/pawgress/issues/3): lint, tests, and hooks.
- [Issue #4](https://github.com/hmke228/pawgress/issues/4): CI. After the workflow
  lands, a maintainer must require its `verify` status check in the
  `cs467_project` ruleset and verify that failing checks block merging.
- [Issue #5](https://github.com/hmke228/pawgress/issues/5): use the existing Project
  Plan. This setup does not replace the plan or establish that team approval and
  MVP backlog acceptance criteria are complete.

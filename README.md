# Pawgress

Pawgress is a Python CLI application for the CS 467 Capstone Project. The planned
application helps owners understand one target dog's observable behaviors and
compare observations over time. The existing team Project Plan defines the
product requirements and architecture.

The Epic 2 CLI connects a saved dog profile, situation and images to sourced
canine references, AI report generation and comparison with up to three relevant
historical reports. Complete reports are saved in SQLite for later analyses.

**New to Pawgress?** Start with [How to Use Pawgress](HOW_TO_USE.md) for installation,
API configuration, your first report, and everyday usage.

## Development setup

Prerequisites: Python 3.13, Git, and a POSIX shell (macOS, Linux, or WSL) for the
commands below. Offline tests need no API keys or database setup.

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

Both entry points print help when called without arguments. Activate `.venv`, set
`OPENAI_API_KEY` securely in your environment, and set `OPENAI_MODEL` to a model
supporting image input and Structured Outputs. Run the interactive dog workflow:

```sh
pawgress --dog
python -m pawgress --dog
```

First use collects a name and description (appearance, basic details and behavioral
background), a situation and at least one PNG/JPEG/WebP image. Enter image paths
one at a time, then `done`. Later runs reuse the profile and allow an empty situation.
Use identifying details to distinguish the target dog in multi-dog images.

Comparison filters same or behaviorally comparable scenes before selecting the
latest **up to three** matches. It never fills with unrelated reports. No matches
means `comparison: null` and `referenced_report_ids: []`. AI fields are preserved.
One API request generates the current report, a second filters existing history,
and a third compares selected matches when any exist. Tests replace HTTP only.

The default database is `~/.local/share/pawgress/pawgress.db`; use
`--db /tmp/pawgress-test.db` for isolated testing. Each database holds one profile
and immutable complete reports; image files are not copied into SQLite. The old
standalone demo table is preserved separately, not imported into Epic 2 history.
The bundled knowledge base currently contains one professional reference. When
the situation is absent or has no keyword match, its general background is used.
Use `--knowledge-base /path/to/references.json` for a reviewed expanded collection.

See the [manual testing guide](docs/epic2_manual_testing.md) for secure key setup, first
and later runs, inspecting saved JSON, and failure cases. The legacy
`pawgress "text"` command remains an Epic 1 demonstration using mock history.

## Project layout and architecture

```text
src/pawgress/
    __init__.py              Python package
    __main__.py              python -m pawgress entry point
    cli.py                   CLI entry point and help
    cli_input.py             Situation and image-path collection
    dog_cli.py               Profile reuse and final dog-report display
    ai.py                    AI response and generator contract
    dog_report.py            Vision request and dog-report content contracts
    openai_generator.py      Structured OpenAI generation
    rag.py                   Sourced knowledge retrieval and context formatting
    knowledge_base.py        Reference validation and loading
    behavioral_comparison.py History filtering, comparison and standalone demo
    pipeline.py              Epic 2 orchestration and legacy Epic 1 text pipeline
    storage.py               SQLite profile and complete-report persistence
tests/unit/                  Direct unit tests and component import tests
tests/integration/           CLI subprocess smoke tests
scripts/lint.sh              Ruff lint and format checks
```

The Project Plan's four main components are CLI, AI Report Generation, RAG, and
Behavioral Comparison. Storage is a supporting module: the team has selected
**SQLite**, using Python's built-in `sqlite3` module. The comparison component has
a standalone database prototype; the integrated Epic 1 pipeline uses mock history.
The integrated Epic 2 pipeline uses the supporting `ReportStore` for persistence.

AI generation uses OpenAI; Epic 1 retains its provider-independent `AIGenerator`
interface. Keep the setup lightweight and follow the existing Project Plan;
changes to requirements or architecture need team approval.

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

## Team workflow

- Work on separate `chore/`, `feat/`, or `fix/` branches; never commit directly to
  `main`. Merge through pull requests with at least one approval and CODEOWNERS review.
- Each PR must have fewer than 100 changed lines, counting additions and deletions.
  Keep PRs focused; an issue may have multiple PRs. Use `Refs #2`, `Refs #3`, or
  `Refs #4`; close issues only after all acceptance criteria are met. Keep #5 open
  for the team's requirements and MVP backlog decisions.
- Add tests with code changes. Unit line coverage must exceed 90% (91% gate).
  Cover public entry points with integration tests; include validation in PRs.
- Use descriptive snake_case names, typed function signatures, and Ruff formatting
  and import ordering. Never commit secrets, virtual environments, or runtime data.
- AI-generated work must be reviewed, understood, and tested; document or cite it
  when required by course policy. Agents follow `AGENTS.md` and need approval to
  commit, push, or publish PRs.

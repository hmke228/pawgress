# Story 3.2: AI quality and schema compliance

Refs #28; parent Epic #26. Evaluation date: 2026-11-18.
Baseline: `fce3658` (the integration branch merged by PR #53).

## Scope

Preserve the five AI text fields and the final report schema. Comparison still
owns historical matching, comparison text and references. No new dependencies,
storage behavior, or retrieval changes are introduced. The shared AI adapter
also applies strict duplicate-field rejection to the legacy text workflow.

## Fixed offline evaluation

`tests/unit/test_ai_quality.py` uses real SDK parsing, the pipeline and temporary
SQLite storage with HTTP response doubles. Image bytes are transport fixtures,
not photographs. The five content fixtures are authored expected responses,
not model-generated outputs or evidence of improved model accuracy.

| Check | Before | After |
| --- | --- | --- |
| First report, comparable history, no comparable history | 3/3 pass | 3/3 pass |
| Missing situation and ambiguous target: preserve supplied uncertainty | 2/2 pass | 2/2 pass |
| Missing, blank, null or numeric value in each of five fields | 20/20 rejected | 20/20 rejected |
| Duplicate value for each of five fields | 5/5 silently accepted, saved and displayed | 5/5 rejected before history requests, saving or display |
| New fixed suite | 25 passed, 5 failed | 30 passed |

Valid fixtures retain all five AI strings, preserve earlier reports, and use
null comparison/empty reference IDs when comparison is unavailable. Malformed
responses produce CLI exit status 1 and a retry message without exposing response
content. Existing tests additionally cover extra fields, malformed JSON, refusal,
incomplete responses and API failures.

## Prompt review

Existing instructions already distinguish observations, owner reports and uncertain
interpretations. Review identified missing explicit guidance for absent situations,
contradictory evidence and unsupported references. The revised instructions:

- Keep profile background separate from the current event when situation is absent.
- Attribute conflicting owner descriptions and visual evidence without resolving
  the discrepancy through invented facts; treat obscured cues as unknown.
- Request clearer evidence when identity or behavior cannot be assessed.
- Limit reference-based interpretation to supported cues and check claim provenance.

This is a prompt inspection result, not a measured improvement in model judgments.
Live comparison of the old and revised prompts is optional, not an acceptance gate.

## Practical acceptance scope

The user clarified the intended MVP acceptance scope on 2026-11-18:

- The application runs through report generation, display and persistence.
- Analysis focuses on the identified target dog. If identity is unclear, state
  the limitation instead of attributing another dog's behavior to the target.
- Reports from the same or behaviorally comparable scenes can be compared with
  relevant history; unrelated history is not used to fill comparison slots.

Professional-level behavioral analysis and a formal prompt-quality benchmark are
outside this acceptance scope. Retain the existing schema and basic safeguards.
The user reports that the complete pipeline works in live testing. Offline tests
verify structure, persistence and comparison handling with controlled responses;
they do not independently verify visual target recognition or live scene matching.
An ordinary demo can check those behaviors without a separate before/after study.

## Reproduction

Run `python -m pytest tests/unit/test_ai_quality.py --no-cov` in `.venv`.
To reproduce the baseline, run the same test file against the baseline production
code; the five duplicate-field cases fail. No credentials or network are required.

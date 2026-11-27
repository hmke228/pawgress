
# RAG Relevance Evaluation

## Purpose

This evaluation was completed for Epic 3, Story 3.3 to improve
the relevance and quality of professional canine behavior references
retrieved by Pawgress.

The goal was to retrieve relevant references for a dog's reported
behavior while avoiding unrelated references when no useful match
was available.

## Before-and-After Results


The results below reflect two improvements: changes to the retrieval
logic and expansion of the professional reference collection. The
no-match improvements came from updating retrieval behavior, while
the additional behavior coverage came from adding new professional
references and improving keyword matching.

| Test Scenario | Before Improvements | After Improvements |
|---|---|---|
| Tucked tail | Retrieved the VCA reference | Retrieved the VCA reference |
| Tail between legs | Retrieved the VCA reference | Retrieved only the relevant VCA reference |
| General nervousness | Returned an unrelated fallback reference | No reference returned |
| Vomiting | Returned an unrelated fallback reference | No reference returned |
| Food guarding | Not covered by the original reference collection | Retrieved the ASPCA Food Guarding reference |
| Barking | Not covered by the original reference collection | Retrieved the ASPCA Barking reference |
| Lip licking and yawning | Not covered by the original reference collection | Retrieved the Merck behavior reference |
| Play bow | No specific reference available | No reference returned |

## Changes Made

- Expanded the professional reference collection from one reference
  to six references using veterinary and animal welfare sources.
- Improved stop-word filtering to reduce irrelevant keyword matches.
- Added normalization for different forms of barking and growling.
- Removed the fallback that returned unrelated references when a
  nonempty query had no relevant matches.
- Added eight offline relevance evaluation cases.
- Updated AI input handling so an empty reference list does not
  prevent report generation.

## Source Quality Review

The reference collection was reviewed for professional provenance,
source attribution, duplicate content, and unsupported claims.

The collection includes sources from VCA Animal Hospitals,
Merck Veterinary Manual, and ASPCA. Each entry includes a unique
reference ID, source title, and URL.

No duplicate entries were identified in the six-reference collection.
The reference passages were written as short summaries rather than
copied directly from the source articles.

## Testing Results

- RAG relevance tests: 8 passed.
- Full project test suite: 347 passed.
- Code coverage: 98.70%.
- Ruff linting and formatting: Passed.

## Limitations and Future Improvements

The retrieval system currently relies on keyword overlap and a
small set of normalized terms rather than semantic similarity.
As a result, some behavior descriptions may not match relevant
references if different vocabulary is used.

When the situation is blank or missing, the current implementation
still supplies the general reference collection. This behavior
may need further review to prevent unrelated context from being
included in image-only assessments.

Additional professionally sourced references and more varied test
queries could improve coverage.

The evaluation fixtures and expanded reference collection should
be reviewed by the team before merging.

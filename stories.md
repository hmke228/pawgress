# Pawgress Epic and Story Outline

Planning index for team discussion. This does not replace the Project Plan,
approve implementation, or finalize the proposed report schema.

## Work on one Epic at a time

- Keep this file as a short outline; expand only the Epic the user requests.
- When asked to read an Epic and generate its Stories, draft only that Epic's
  descriptions and acceptance criteria. Do not expand all three Epics at once.
- Create or update GitHub issues only when requested. Check the existing issue
  links below first; do not create duplicates.
- A request to draft Stories does not authorize code implementation.
- Keep Stories small for a four-person team; do not assign owners or deadlines yet.
- Requirements, architecture, and unresolved interfaces remain subject to team review.

## Epic 1 — Build Minimal End-to-End Pipeline

**Make the pipeline work.** Use a tiny text example, a small test knowledge base,
and minimal data structures. The example does not need to involve dogs; use
mock/test data where appropriate. Exclude dog profiles, images, and the full
Pawgress report schema.

Existing Epic: [#16](https://github.com/hmke228/pawgress/issues/16).

| Story | Small outcome | Existing issue |
| --- | --- | --- |
| 1.1 CLI / Input | Accept simple text through the CLI. | [#17](https://github.com/hmke228/pawgress/issues/17) |
| 1.2 AI / Report Generation | Generate a basic structured response from input and retrieved context. | [#18](https://github.com/hmke228/pawgress/issues/18) |
| 1.3 RAG / Knowledge Retrieval | Retrieve relevant information from a small test knowledge base. | [#19](https://github.com/hmke228/pawgress/issues/19) |
| 1.4 History / Comparison | Save results, retrieve one relevant previous entry, and demonstrate a simple comparison. | [#20](https://github.com/hmke228/pawgress/issues/20) |

## Epic 2 — Implement Pawgress Dog Behavior MVP

**Make Pawgress work.** Extend the working Epic 1 pipeline to one dog's behavior
analysis. Reference the preliminary [schema design](docs/research/ai_report_schema.md)
when this Epic is discussed; do not modify or implement it merely to draft Stories.
Schema, scene matching, storage details, and interfaces still need team review.
Populate the professional knowledge base before generating the first dog report.

Existing Epic: [#21](https://github.com/hmke228/pawgress/issues/21).

| Story | Small outcome | Existing issue |
| --- | --- | --- |
| 2.1 CLI / Input | Collect/reuse one dog profile; accept multiple images and situation descriptions, optional on later runs. | [#22](https://github.com/hmke228/pawgress/issues/22) |
| 2.2 AI / Report Generation | Generate structured dog behavior reports using the team-reviewed Pawgress schema. | [#23](https://github.com/hmke228/pawgress/issues/23) |
| 2.3 RAG / Knowledge Retrieval | Retrieve relevant professional canine behavior references. | [#24](https://github.com/hmke228/pawgress/issues/24) |
| 2.4 History / Comparison | Coordinate immutable report storage, previous-report matching, and comparison with up to three relevant reports. | [#25](https://github.com/hmke228/pawgress/issues/25) |

### History matching and comparison responsibility

The teammate responsible for History / Comparison coordinates previous-report
matching, selection, and comparison in Story 2.4, and their refinement in Story 3.4.
This defines the work scope without assigning a named team member. At the component
level, RAG retrieves historical reports, Behavioral Comparison compares observations,
and supporting Storage saves and reads records. Story 2.3 focuses on professional
canine references; historical retrieval is coordinated through Story 2.4.

- First identify reports with behaviorally comparable scene contexts; scenes need
  not be identical, and shared environmental keywords alone do not establish relevance.
- Sort relevant matches by `created_at` descending and select up to three reports.
- Use fewer when fewer relevant reports exist; never fill with unrelated reports.
- Compare current observations with the selected history, acknowledging environmental
  differences and limited photographic evidence; return only actually referenced IDs.
- With no comparable history, return `comparison: null` and `referenced_report_ids: []`.
- The matching algorithm remains TBD pending team discussion; this is not an
  implementation decision or a change to the preliminary schema.

## Epic 3 — Improve Quality, Reliability, and UX

**Make Pawgress work well.** Improve the working Epic 2 MVP without major new
features or unapproved schema/architecture changes.

Existing Epic: [#26](https://github.com/hmke228/pawgress/issues/26).

| Story | Small outcome | Existing issue |
| --- | --- | --- |
| 3.1 CLI / Input | Improve validation, error handling, and usability. | [#27](https://github.com/hmke228/pawgress/issues/27) |
| 3.2 AI / Report Generation | Improve prompts, report consistency, and schema compliance. | [#28](https://github.com/hmke228/pawgress/issues/28) |
| 3.3 RAG / Knowledge Retrieval | Improve retrieval relevance and knowledge-source quality. | [#29](https://github.com/hmke228/pawgress/issues/29) |
| 3.4 History / Comparison | Improve similarity matching and verify historical references and comparisons. | [#30](https://github.com/hmke228/pawgress/issues/30) |

## Existing GitHub backlog

The 3 Epics and 12 Stories above were already created, with native parent/sub-issue
links. They are proposals for review, not completed work or approved implementation.
This outline does not close, delete, or update them. Keep
[#5](https://github.com/hmke228/pawgress/issues/5) open for team requirements and
MVP backlog finalization. Storage remains a supporting module using standard-library
`sqlite3`, not a fifth main component.

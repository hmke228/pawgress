# Pawgress MVP Schema Design (v1)

Epic 2 AI working contract: RAG supplies professional knowledge to AI; Comparison owns historical report storage, retrieval and filtering through its database. Prioritize a functional end-to-end MVP with minimal variables and nesting. The standalone AI entry point is described below; the CLI still runs the Epic 1 pipeline.

## 1. MVP Scope

- Analyze one target dog. Collect its basic profile and behavioral background once, save them, and reuse them for future analyses.
- Accept multiple photos and a detailed free-text situation description. For subsequent reports, the new situation description is optional.
- The general canine behavior knowledge base has **not been populated yet**. It must contain reliable professional canine behavior references **before the first report is generated**. Researching, collecting, and organizing these resources are separate work handled by the RAG component.
- Save every generated report for future retrieval, with a unique `report_id` and `created_at`; never overwrite previous reports. Prioritize historical reports with behaviorally relevant scene similarity rather than simply selecting the three most recent reports.

## 2. First Report: No Previous Reports

Collect the dog's basic information, behavioral background (in `description`), situation, and photos. Save the profile for reuse.

```json
{
  "dog_profile": {
    "name": "Promise", "breed": "Golden Retriever", "age": 2,
    "color": "Golden", "sex": "female", "neutered": true,
    "description": "Friendly and playful"
  },
  "situation": "At a dog park, another dog approached Promise. She started barking and jumping. I want to know whether this was playful or aggressive.",
  "image_paths": ["photo1.jpg", "photo2.jpg"]
}
```

The first report must use professional canine behavior knowledge retrieved by RAG, even though no previous reports exist. This requires the knowledge base to be populated before generation begins. The following source and content are placeholders, not real citations.

```json
{
  "canine_knowledge": [{"source": "Professional canine behavior reference", "content": "Relevant canine body language and behavior information"}]
}
```

AI uses the saved dog profile, user-provided situation, submitted images, and retrieved professional knowledge to generate the first report, including scene context and current observations. This establishes an initial behavioral baseline.

## 3. Subsequent Reports: Previous Reports Exist

Automatically load the saved dog profile. Collect new photos and an optional new situation description.

```json
{
  "situation": "Promise met another dog again today. She seemed more relaxed.",
  "image_paths": ["photo3.jpg", "photo4.jpg"]
}
```

For both first and subsequent reports, AI generates `scene_context` using the user's free-text `situation` description from the CLI (when supplied) and environmental details observable in the submitted images. It also produces current behavioral observations. Keep `scene_context` as one descriptive field covering relevant surroundings (such as indoor/outdoor setting, other dogs, people, and activity). Distinguish user-reported information from directly observable visual evidence in the wording, without adding schema variables. For example, other dogs mentioned by the owner but absent from the images may contribute to scene context as user-reported information, but must not be presented as confirmed visual observations. Do not invent environmental conditions.

1. Behavioral Comparison retrieves historical reports from its own database and filters them using current `scene_context`; exact matches or shared environmental keywords alone do not determine comparability. For example, whether outdoor with multiple dogs, indoor with multiple dogs, or outdoor with one dog is most comparable depends on the specific behavior being analyzed. The Comparison teammate decides the matching algorithm; it is not implemented here.
2. Sort matching reports by `created_at` descending (newest first), then select up to three. Return fewer when fewer relevant reports exist; never fill the result with unrelated reports.
3. AI passes the current report to Behavioral Comparison, which reads selected historical IDs, timestamps, scene contexts and observations from its database.
4. Comparison compares current observations with selected history and produces a short summary plus actually referenced IDs. The Comparison teammate decides whether to use OpenAI for this summary. Acknowledge environmental differences and limited photographic evidence; do not automatically label changes as improvement or regression.
5. Behavioral Comparison fills `comparison` and `referenced_report_ids`, preserves all other AI content, saves the final report and returns it to CLI. With no comparable history, retain `comparison: null` and an empty ID list. RAG does not handle report history; AI does not integrate comparison results.

## 4. Final Report Schema

Reuse this schema for first and subsequent reports. The Project Plan's three report sections remain **Safety Assessment**, **Behavioral Observations**, and **Recommendations**. History comparison is nested within Behavioral Observations; IDs, timestamp, and scene context are supporting metadata.

```json
{
  "report_id": "report_002",
  "created_at": "2026-10-20T12:00:00Z",
  "scene_context": "Outdoor, another dog present",
  "safety_assessment": "Potential safety concerns and limitations",
  "behavioral_observations": {
    "observations": "Current evidence about the target dog; distinguish owner reports from images",
    "interpretation": "Possible explanations grounded in professional references, with uncertainty",
    "comparison": "Comparison with relevant previous reports"
  },
  "recommendations": "Suggestions for the owner",
  "referenced_report_ids": ["report_001"]
}
```

For the first report, `comparison` is `null` and `referenced_report_ids` is `[]`. The application generates each unique `report_id` and ISO 8601 UTC `created_at` timestamp for chronological ordering; the AI does not invent them. Save every report as a new record available for later retrieval.

## 5. End-to-End Data Flow

**First report:** CLI collects profile + situation + images and the application saves the profile → RAG retrieves professional canine knowledge → AI generates current report content → application assigns ID and timestamp → Comparison finds no history in its database, retains empty comparison fields and saves the final report → CLI displays the final report.

**Subsequent reports:** CLI provides saved profile + optional situation + images → RAG provides professional knowledge → AI generates current report content → application assigns ID and timestamp → Comparison retrieves and filters its database history using current scene context, compares observations with up to three relevant reports and fills comparison fields → Comparison saves the final report → CLI displays it. No comparable history uses the same empty fields as the first report; exclude the current report from history.

## 6. Component Interfaces

| Component | Receives and provides |
| --- | --- |
| CLI | Collects profile, situation, and images; loads the saved profile for later analyses; displays the final report. |
| AI Report Generation | Receives profile, situation, images and professional references; produces current scene, observations, interpretation, safety assessment and recommendations. |
| RAG | Collects and retrieves professional canine behavior references for AI; does not store, retrieve or filter historical reports. |
| Behavioral Comparison | Receives the current AI report; owns history storage, retrieval and filtering in its database; generates comparison, optionally using OpenAI; fills comparison and actually referenced IDs, preserves other AI fields, saves and returns the final report to CLI. |

Comparison owns report persistence and historical queries through its database; profile persistence remains application support. The planned storage technology remains standard-library `sqlite3`, with Storage as a supporting module. This AI change does not implement database schemas, queries or storage interfaces.

## 7. Design Principles and Open Questions

Keep the MVP minimal and reuse one report schema. Exclude multi-dog management, user accounts, complex behavior scoring, and advanced trend detection. Do not make medical or behavioral diagnoses; acknowledge uncertainty when image evidence is insufficient. Comparison owns the remaining scene-matching and report-storage implementation decisions; concrete integration interfaces remain to be coordinated.

## 8. Standalone AI entry point

`OpenAIGenerator.generate_dog_report(DogReportInput(...))` accepts the profile, ordered `image_paths`, nonempty `canine_knowledge` entries with `source`/`content`, optional `situation`, and optional `target_hint` identifying dog A among other dogs. Profile `name` and behavioral `description` must be nonblank. Reference quality remains RAG's responsibility; historical reports go downstream, not into current observations.

The adapter embeds PNG/JPEG/WebP bytes in order and checks file signatures, not complete image validity. Image order does not prove continuous motion. The configured model must support vision and Structured Outputs. The five flat AI strings are validated, then `DogReport.to_report_content()` nests observations/interpretation and initializes comparison to `null` and referenced IDs to `[]`; application ID/time are still required before persistence. This replaces the proposed `current` field without modifying the Epic 1 comparison implementation.

Pending integration: RAG retrieval when situation is absent; historical matching/filtering; CLI image validation; application metadata and persistence. Offline fixtures verify transport and structure, not real model accuracy or target recognition. API formats follow OpenAI's [image input](https://developers.openai.com/api/docs/guides/images-vision?api-mode=responses) and [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses) documentation.

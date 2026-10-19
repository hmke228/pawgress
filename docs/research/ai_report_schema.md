# Pawgress MVP Schema Design (v1)

Proposed research and design for team discussion; interfaces are pending review. Prioritize a functional end-to-end MVP with minimal variables and nesting. This document does not implement the schema or change the Project Plan.

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
  "canine_knowledge": [{"source": "Professional canine behavior reference", "content": "Relevant canine body language and behavior information"}],
  "previous_reports": []
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

1. Identify behaviorally relevant historical reports based on `scene_context`; exact matches or shared environmental keywords alone do not determine comparability. For example, whether outdoor with multiple dogs, indoor with multiple dogs, or outdoor with one dog is most comparable depends on the specific behavior being analyzed. The scene-matching algorithm is **TBD — Pending Team Discussion**; do not implement it yet.
2. Sort matching reports by `created_at` descending (newest first), then select up to three. Return fewer when fewer relevant reports exist; never fill the result with unrelated reports.
3. Give Behavioral Comparison the current scene context and observations plus the selected reports' IDs, timestamps, scene contexts, and observations.
4. Compare current behavior with those historical observations. Return a short comparison summary and the IDs of reports actually referenced. Acknowledge environmental differences and limited photographic evidence; do not automatically label changes as improvement or regression.
5. AI incorporates the comparison into Behavioral Observations. With no comparable history, use `comparison: null` and an empty `referenced_report_ids` array to indicate that comparison is unavailable.

## 4. Final Report Schema

Reuse this schema for first and subsequent reports. The Project Plan's three report sections remain **Safety Assessment**, **Behavioral Observations**, and **Recommendations**. History comparison is nested within Behavioral Observations; IDs, timestamp, and scene context are supporting metadata.

```json
{
  "report_id": "report_002",
  "created_at": "2026-10-20T12:00:00Z",
  "scene_context": "Outdoor, another dog present",
  "safety_assessment": "Potential safety concerns and limitations",
  "behavioral_observations": {
    "current": "Current observations and possible interpretations",
    "comparison": "Comparison with relevant previous reports"
  },
  "recommendations": "Suggestions for the owner",
  "referenced_report_ids": ["report_001"]
}
```

For the first report, `comparison` is `null` and `referenced_report_ids` is `[]`. The application generates each unique `report_id` and ISO 8601 UTC `created_at` timestamp for chronological ordering; the AI does not invent them. Save every report as a new record available for later retrieval.

## 5. End-to-End Data Flow

**First report:** CLI collects profile + situation + images → RAG retrieves professional canine knowledge → AI analyzes images and generates the initial report → application assigns ID and timestamp → report and profile are saved → CLI displays the report.

**Subsequent reports:** CLI collects optional situation + images → saved profile is loaded → AI performs initial analysis and generates scene context from the supplied situation and observable image details → RAG retrieves relevant canine knowledge and finds behaviorally relevant historical reports based on scene context → matching reports are sorted newest first and limited to three → Behavioral Comparison compares observations → AI integrates comparison into the final report → application assigns new ID and timestamp → new report is saved → CLI displays the report.

## 6. Component Interfaces

| Component | Receives and provides |
| --- | --- |
| CLI | Collects profile, situation, and images; loads the saved profile for later analyses; displays the final report. |
| AI Report Generation | Receives profile, situation, images, professional references, and comparison results; produces scene context, current observations, and final report content. |
| RAG | Uses situation and scene context to provide professional references and retrieve relevant historical reports, including IDs, timestamps, scene contexts, and observations. |
| Behavioral Comparison | Receives current scene context, observations, and up to three relevant previous reports; returns a short comparison summary and actually referenced report IDs. |

Persistent storage saves the profile and reports; RAG retrieves relevant information from saved data and the professional knowledge base. Storage is a supporting module using the planned standard-library `sqlite3`; database schemas, queries, and storage interfaces are not finalized or implemented here.

## 7. Design Principles and Open Questions

Keep the MVP minimal and reuse one report schema. Exclude multi-dog management, user accounts, complex behavior scoring, and advanced trend detection. Do not make medical or behavioral diagnoses; acknowledge uncertainty when image evidence is insufficient. Team review must resolve scene matching, storage details, and final interfaces before implementation.

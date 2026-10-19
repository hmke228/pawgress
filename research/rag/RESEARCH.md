# Pawgress RAG Prototype – Initial Research and Testing

## Overview

For my initial RAG development work, I created a small Python retrieval prototype to explore how Pawgress could search a canine behavior knowledge base. The prototype uses TF-IDF with scikit-learn to compare behavioral observations against sample reference entries stored in a JSON file.

The goal was to understand how retrieval could support the AI report generation component before implementing the complete RAG system.

## Development Setup

- Python 3.13.16
- Conda environment: `pawgress`
- scikit-learn 1.9.1
- Git branch: `research/rag-prototype`

## Implementation

I created two files:

- `sample_knowledge.json`: Contains five original demonstration entries related to canine behavior.
- `prototype.py`: Loads the JSON file, converts the reference text and user query into TF-IDF vectors, calculates cosine similarity, and returns up to three matching entries.

The prototype currently runs independently from the main Pawgress application.

## Initial Testing

| Search Query | Expected Topic | Top Result | Similarity |
|---|---|---|---|
| dog has a tucked tail and lowered body posture | stress_signals | stress_signals | 0.546 |
| dog holds its ears backward | ear_position | ear_position | 0.490 |
| dog performs a play bow with loose movements | play_behavior | play_behavior | 0.421 |
| dog suddenly becomes stiff and still | body_tension | body_tension | 0.234 |
| airplane engine maintenance | No match | No match | N/A |

The prototype returned the expected top result for all five test cases.

## Findings and Limitations

TF-IDF was relatively straightforward to implement and successfully retrieved matching information from the small demonstration knowledge base.

However, this approach depends heavily on overlapping words between the query and the stored reference entries. It may struggle when different terminology is used to describe the same behavior.

The prototype also returned some less relevant secondary results because it currently accepts any positive similarity score.

The similarity scores represent textual similarity, not confidence in a behavioral interpretation.

These results are limited to five demonstration entries and do not establish retrieval accuracy on real veterinary reference material.

## Next Steps

- Expand the knowledge base using reviewed canine behavior resources.
- Track source titles, URLs, and usage permissions.
- Evaluate embedding-based retrieval as an alternative.
- Implement more systematic retrieval testing.
- Coordinate the retrieval interface with the AI report generation component.
- Integrate the RAG component into the Pawgress application.

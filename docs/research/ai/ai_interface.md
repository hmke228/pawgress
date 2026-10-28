# Epic 1 AI interface — proposed for team agreement

`AIGenerator.generate(user_input: str, rag_context: str) -> AIResponse` is a
synchronous typing contract only; no client, generation, or input validation exists.
Serialize the immutable two-string response with `dataclasses.asdict(response)`.
Team agreement is needed on nonblank outputs, empty-context handling, converting
current RAG records to text, and the Comparison handoff. Proposed: Comparison
receives both fields, compares only observations, and preserves interpretation.
Its research models use a different shape; no adapter or Epic 2 schema is added.
String validation cannot verify accuracy or uncertainty. No second AI step is added.

# Behavioral Comparison

## Goal

The Behavioral Comparison component is responsible for comparing a dog's current behavioral observations against up to three relevant historical reports and producing a concise summary of what has remained consistent and what has changed over time.

This component does not generate behavioral interpretations or recommendations. Its purpose is to identify similarities and differences between current and historical observations and provide that information to the AI Report Generation component.

Responsibilities:

- Receive the current scene context and behavioral observations.
- Retrieve up to three relevant historical reports for the same dog from SQLite, with selection informed by scene context.
- Compare current observations with historical observations.
- Identify behaviors or themes that:
  - Remain consistent across reports.
  - Appear in the current report but not in historical reports.
  - Appeared in historical reports but are not present in the current report.
- Generate a short comparison summary.
- Return the IDs of the reports that were actually used in the comparison.
- Store the current dog report in SQLite after comparison so it is available to future comparisons.

The first report for a dog has no historical data available. Return a baseline indicator and store the report for future comparisons. A report must not be included in its own historical results.


## Research & Design Ideas

The behavioral component's purpose is not to perform behavioral analysis. Behavioral interpretation is already handled by AI Report Generation using image analysis, user context, and retrieved canine behavior references.

Instead, the comparison component should focus on:

- Similarities between current and previous observations.
- New observations appearing in the current report.
- Previously observed behaviors that are no longer mentioned.

### Prototype Approach

Rapid prototype implementation:

1. Receive current observations.
2. Receive 0–3 relevant previous reports.
3. Extract simple observation themes or keywords.
4. Determine:
   - Consistent observations
   - Newly observed behaviors
   - Behaviors no longer observed
5. Generate a concise comparison summary.
6. Return referenced report IDs.

### Design Considerations

- Keep the comparison engine deterministic and explainable.
- Avoid duplicating AI Report Generation responsibilities.
- Support 0–3 historical reports.
- Handle "first report" scenarios gracefully.
- Focus on tracking observations rather than determining emotional state.
- Maintain a lightweight implementation suitable for an MVP and capstone scope.

## Proposed Schema / Structure

### Workflow

```text
Current Dog Report
         ↓
Retrieve up to 3 relevant prior reports for this dog from SQLite
         ↓
Extract observation themes from current and historical reports
         ↓
Compare current observations with historical themes
         ↓
Summarize:
- Consistent observations
- Newly observed behaviors
- Previously observed behaviors not mentioned in the current report
         ↓
Return summary + IDs of reports used
         ↓
Store current dog report in SQLite
```

### First Report Workflow

```text
First Current Dog Report
         ↓
Query SQLite for prior reports for this dog
         ↓
No prior reports found
         ↓
Return baseline indicator
         ↓
Store current report in SQLite
```

## Open Questions

### Historical Report Selection

- Will the Behavioral Comparison module receive the id's of behaviorally relevant historical reports based on scene_context from the AI or will this have to be done by this module?
- What scene-matching algorithm should be used to identify the relevant historical reports?

## References

Add useful documentation or resources.

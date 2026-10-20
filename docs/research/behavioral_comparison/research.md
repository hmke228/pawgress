# Behavioral Comparison Module

The behavioral comparison module is intended to compare a dog's current
behavioral analysis with its previous reports and classify the overall trend.
It is organized into report data, report history, comparison logic, and trend
classification.

## Files

- **`models.py` — `BehavioralReport`:** Defines the report structure: report and
  dog IDs, stress, sociability, confidence, and reactivity scores, an
  AI-generated summary, and a creation timestamp. If no timestamp is supplied,
  it is set to the current local time.
- **`enums.py` — `Trend_Category`:** Defines the possible classifications:
  `IMPROVEMENT`, `REGRESSION`, `STABLE`, `MIXED`, and `INSUFFICIENT_HISTORY`.
- **`report_repository.py` — `ReportRepository`:** Reserves methods to retrieve
  reports for a dog, save a report, and retrieve the latest report. These are
  currently TODO placeholders; report storage and retrieval are not implemented.
- **`comparison_engine.py` — `Comparison_Engine`:** Provides a skeleton for
  comparing a current report with historical reports. It currently returns
  `None` when fewer than two historical reports are supplied; calculating
  metric changes and determining a trend remain TODOs.
- **`trend_classifier.py` — `Trend_Classifier`:** Classifies metric changes.
  Decreases in stress and reactivity and increases in sociability and confidence
  count as favorable. Missing metric changes produce `INSUFFICIENT_HISTORY`.
  Meaningful changes (absolute value of at least 0.5) in both favorable and
  unfavorable directions produce `MIXED`. Otherwise, a net favorable score
  greater than 3 produces `IMPROVEMENT`, below -3 produces `REGRESSION`, and
  values between those thresholds produce `STABLE`.

## Current status

The report model and trend classifier contain working behavior. The repository
and comparison engine are scaffolds, so the module does not yet fetch or store
historical reports or calculate changes between reports. The classifier also
expects metric changes as inputs; connecting it to the comparison engine is
future work.

## Trend classification rules

Metric changes are calculated as current score minus previous score. The
classifier converts each change into a favorable direction: decreases in stress
and reactivity count as positive, while increases in sociability and confidence
count as positive.

| Trend | Rule implemented in `Trend_Classifier` |
| --- | --- |
| **Improvement** | No meaningful changes conflict, and the sum of favorable-direction changes is greater than 3. |
| **Regression** | No meaningful changes conflict, and the sum of favorable-direction changes is less than -3. |
| **Stable** | No meaningful changes conflict, and the sum of favorable-direction changes is between -3 and 3, inclusive. |
| **Mixed** | At least one favorable-direction change is 0.5 or greater and at least one is -0.5 or less. |
| **Insufficient history** | At least one metric change is unavailable (`None`). The comparison-engine skeleton also returns `None` when fewer than two historical reports are supplied. |

The classifier applies these rules to all four metrics. It does not require
every metric in the improvement or regression examples to move in the same
direction; instead it uses the net favorable-direction score and the mixed
change rule above. The comparison engine is still a skeleton, so calculating
the changes and deciding how its `None` result maps to
`INSUFFICIENT_HISTORY` remain future work.
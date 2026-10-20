from .enums import Trend_Category


class Trend_Classifier:
    """Classify behavioral trends from changes in report metrics."""

    def classify(
        self,
        stress_change: float | None,
        sociability_change: float | None,
        confidence_change: float | None,
        reactivity_change: float | None,
    ) -> Trend_Category:
        """Classify changes, where positive values mean the metric increased.

        Lower stress and reactivity, and higher sociability and confidence, are
        treated as favorable. Any missing change makes the overall trend
        insufficient to classify.
        """
        if (
            stress_change is None
            or sociability_change is None
            or confidence_change is None
            or reactivity_change is None
        ):
            return Trend_Category.INSUFFICIENT_HISTORY

        favorable_changes = (
            -stress_change,
            sociability_change,
            confidence_change,
            -reactivity_change,
        )
        significant_changes = [
            change for change in favorable_changes if abs(change) >= 0.5
        ]
        has_improvement = any(change > 0 for change in significant_changes)
        has_regression = any(change < 0 for change in significant_changes)

        if has_improvement and has_regression:
            return Trend_Category.MIXED

        overall_change = sum(favorable_changes)
        if overall_change > 3:
            return Trend_Category.IMPROVEMENT
        if overall_change < -3:
            return Trend_Category.REGRESSION
        return Trend_Category.STABLE

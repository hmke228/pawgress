from enum import Enum


class Trend_Category(Enum):
    """Trend classifications for comparing a dog's behavior over time."""

    IMPROVEMENT = "Improvement"
    REGRESSION = "Regression"
    STABLE = "Stable"
    MIXED = "Mixed"
    INSUFFICIENT_HISTORY = "Insufficient History"

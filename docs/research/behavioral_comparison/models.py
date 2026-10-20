from datetime import datetime


class BehavioralReport:
    """A dog's AI-generated behavioral analysis and its recorded scores."""

    def __init__(
        self,
        report_id: str,
        dog_id: str,
        stress_score: float,
        sociability_score: float,
        confidence_score: float,
        reactivity_score: float,
        summary: str,
        created_at: datetime | None = None,
    ) -> None:
        self.report_id = report_id
        self.dog_id = dog_id
        self.stress_score = stress_score
        self.sociability_score = sociability_score
        self.confidence_score = confidence_score
        self.reactivity_score = reactivity_score
        self.summary = summary
        self.created_at = created_at if created_at is not None else datetime.now()

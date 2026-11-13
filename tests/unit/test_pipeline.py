"""Exercise real RAG, AI parsing, and comparison with offline HTTP responses."""

import json
from datetime import datetime, timedelta
from unittest.mock import patch

import httpx
import pytest
from openai import OpenAI

from pawgress.cli import main
from pawgress.pipeline import generate_report


@pytest.mark.parametrize("text", ["My dog has a tucked tail.", "airplane maintenance"])
def test_pipeline_preserves_ai_fields(
    text: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    fields = {
        "observations": "  The dog barked and jumped.  ",
        "interpretation": "  Its emotional state is uncertain.\n",
    }
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body = json.loads(request.content)
        context = (
            "[entry_1] A tucked tail can be a sign of fear or discomfort."
            if "tail" in text
            else ""
        )
        assert json.loads(body["input"]) == {"user_input": text, "rag_context": context}
        assert body["model"] == "test-model"
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(fields),
                                "annotations": [],
                            }
                        ],
                    }
                ],
            },
        )

    with (
        OpenAI(
            http_client=httpx.Client(transport=httpx.MockTransport(handle))
        ) as client,
        patch("pawgress.pipeline.OpenAI", return_value=client),
        patch(
            "pawgress.pipeline.compare_reports",
            return_value={
                "comparison_summary": (
                    "Consistent observations include barking. "
                    "Newly observed behaviors include jumping. "
                    "Previously observed behaviors not mentioned in the current report "
                    "include relaxed posture."
                ),
                "referenced_report_ids": ["epic1-mock-history"],
            },
        ),
        patch("sqlite3.connect", side_effect=AssertionError("No database in Epic 1")),
    ):
        report = generate_report(text)
    created_at = report.pop("created_at")
    assert datetime.fromisoformat(created_at).utcoffset() == timedelta(0)
    assert report == {
        **fields,
        "comparison": (
            "Consistent observations include barking. "
            "Newly observed behaviors include jumping. "
            "Previously observed behaviors not mentioned in the current report "
            "include relaxed posture."
        ),
    }
    assert len(requests) == 1


@pytest.mark.parametrize("missing", ["OPENAI_API_KEY", "OPENAI_MODEL"])
def test_cli_missing_config(
    missing: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.delenv(missing)
    assert main(["The dog barked."]) == 1
    output = capsys.readouterr()
    assert "Set OPENAI_API_KEY and OPENAI_MODEL" in output.err
    assert output.out == ""

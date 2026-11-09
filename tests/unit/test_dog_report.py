"""Offline Epic 2 adapter checks; fixtures do not evaluate model accuracy."""

import base64
import json
from dataclasses import asdict
from pathlib import Path

import httpx
import pytest
from openai import OpenAI

from pawgress.ai import AIGenerationError
from pawgress.dog_report import DogReportInput
from pawgress.openai_generator import OpenAIGenerator

REPORT = {
    "observations": "Image 1: the target's tail is obscured. Owner reports barking.",
    "interpretation": "Emotion is uncertain; stills cannot confirm barking.",
    "scene_context": "Outdoors with another dog; owner reports an approach.",
    "safety_assessment": "Limited evidence; safety cannot be established from stills.",
    "recommendations": "Allow space and observe; no diagnosis can be made here.",
}


@pytest.fixture(params=[b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"RIFF0000WEBP"])
def request_data(tmp_path: Path, request: pytest.FixtureRequest) -> DogReportInput:
    # Synthetic signatures test transport, not image decoding or recognition.
    paths = [tmp_path / "first.png", tmp_path / "second.png"]
    for index, path in enumerate(paths):
        path.write_bytes(request.param + bytes([index]))
    return DogReportInput(
        {"name": "Promise", "description": "Usually playful; owner report."},
        paths,
        [{"source": "Offline test reference", "content": "Consider context."}],
        target_hint="The golden dog with a red collar",
    )


@pytest.mark.parametrize("situation", [None, "Another dog approached; Promise barked."])
@pytest.mark.parametrize(
    "output",
    [
        REPORT,
        {k: v for k, v in REPORT.items() if k != "scene_context"},
        REPORT | {"comparison": "Invented history"},
        REPORT | {"observations": " "},
        REPORT | {"recommendations": 42},
        "bad JSON",
    ],
)
def test_generate_dog_report(
    request_data: DogReportInput, situation: str | None, output: dict | str
) -> None:
    request_data.situation = situation

    def handle(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        content = body["input"][0]["content"]
        expected_text = asdict(request_data)
        del expected_text["image_paths"]
        assert json.loads(content[0]["text"]) == expected_text
        assert [
            base64.b64decode(part["image_url"].split(",")[1]) for part in content[1:]
        ] == [p.read_bytes() for p in request_data.image_paths]
        assert body["store"] is False
        schema = body["text"]["format"]
        assert schema["strict"] is True
        assert set(schema["schema"]["required"]) == set(REPORT)
        assert schema["schema"]["additionalProperties"] is False
        text = json.dumps(output) if isinstance(output, dict) else output
        part = {"type": "output_text", "text": text, "annotations": []}
        message = {"type": "message", "role": "assistant", "content": [part]}
        return httpx.Response(200, json={"status": "completed", "output": [message]})

    with OpenAI(
        api_key="offline-test",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
    ) as client:
        generator = OpenAIGenerator(client, "test-model")
        if output != REPORT:
            with pytest.raises(AIGenerationError, match="invalid"):
                generator.generate_dog_report(request_data)
        else:
            report = generator.generate_dog_report(request_data)
            payload = report.to_report_content()
            observations = payload["behavioral_observations"]
            assert observations == {
                key: REPORT[key] for key in ("observations", "interpretation")
            } | {"comparison": None}
            assert payload["referenced_report_ids"] == []
            for key in ("scene_context", "safety_assessment", "recommendations"):
                assert payload[key] == REPORT[key]
            observations["comparison"] = "Downstream summary"
            assert (
                report.to_report_content()["behavioral_observations"]["comparison"]
                is None
            )


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("dog_profile", {"name": "Promise"}, ValueError),
        ("canine_knowledge", [], ValueError),
        ("canine_knowledge", [{"source": "", "content": "Text"}], ValueError),
        ("situation", 42, TypeError),
        ("target_hint", None, TypeError),
        ("image_paths", [], ValueError),
        ("image_paths", ["missing.png"], ValueError),
    ],
)
def test_invalid_input_before_request(
    request_data: DogReportInput, field: str, value: object, error: type[Exception]
) -> None:
    setattr(request_data, field, value)
    with pytest.raises(error):
        request_data.to_input()


@pytest.mark.parametrize("data", [b"not an image", b""])
def test_invalid_image_bytes(request_data: DogReportInput, data: bytes) -> None:
    request_data.image_paths[0].write_bytes(data)
    with pytest.raises(ValueError, match="image bytes"):
        request_data.to_input()

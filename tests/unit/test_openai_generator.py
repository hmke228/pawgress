"""Adapter unit tests using local HTTP responses, never the live API."""

import json
from unittest.mock import patch

import httpx
import pytest
from openai import OpenAI

from pawgress.ai import AIGenerationError, AIResponse
from pawgress.openai_generator import OpenAIGenerator, main

VALID_TEXT = '{"observations":"Blink.","interpretation":"Maybe."}'


@pytest.mark.parametrize(
    ("text", "status", "refusal", "expected"),
    [
        (VALID_TEXT, "completed", False, None),
        ("not JSON", "completed", False, "invalid"),
        ('{"observations":"A light blinks."}', "completed", False, "invalid"),
        ('{"observations":1,"interpretation":"Maybe."}', "completed", False, "invalid"),
        ('{"observations":" ","interpretation":"?"}', "completed", False, "invalid"),
        ("[]", "completed", False, "invalid"),
        ("", "completed", False, "invalid"),
        ("{}", "incomplete", False, "not completed"),
        ("", "completed", True, "refused"),
    ],
)
@pytest.mark.parametrize("context", ["", "Blinking may indicate readiness."])
def test_response_handling(
    text: str, status: str, refusal: bool, expected: str | None, context: str
) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert json.loads(body["input"]) == {
            "user_input": "A light blinks.",
            "rag_context": context,
        }
        assert body["model"] == "test-model"
        assert body["text"]["format"]["strict"] is True
        assert body["store"] is False
        content = (
            {"type": "refusal", "refusal": "Declined"}
            if refusal
            else {"type": "output_text", "text": text, "annotations": []}
        )
        message = {"type": "message", "role": "assistant", "content": [content]}
        return httpx.Response(200, json={"status": status, "output": [message]})

    with OpenAI(
        api_key="offline-test",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
    ) as client:
        generator = OpenAIGenerator(client, "test-model")
        if expected:
            with pytest.raises(AIGenerationError, match=expected):
                generator.generate("A light blinks.", context)
        else:
            assert generator.generate("A light blinks.", context) == AIResponse(
                "Blink.", "Maybe."
            )


@pytest.mark.parametrize("status", [401, 429, 500, None])
def test_api_failures(status: int | None) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        if status is None:
            raise httpx.ReadTimeout("Timed out", request=request)
        return httpx.Response(status, json={"error": {"message": "Test failure"}})

    with OpenAI(
        api_key="offline-test",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
    ) as client:
        with pytest.raises(AIGenerationError, match="request failed"):
            OpenAIGenerator(client, "test-model").generate("A light blinks.", "Context")


@pytest.mark.parametrize(
    ("user_input", "context", "error"),
    [(None, "Context", TypeError), ("Text", None, TypeError), (" \t", "", ValueError)],
)
def test_invalid_input(
    user_input: object, context: object, error: type[Exception]
) -> None:
    def reject_request(request: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid input must not send an API request")

    with OpenAI(
        api_key="offline-test",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(reject_request)),
    ) as client:
        with pytest.raises(error):
            OpenAIGenerator(client, "test-model").generate(user_input, context)


@pytest.mark.parametrize("failed", [False, True])
def test_demo_result(
    failed: bool, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    response = AIResponse(
        "The dog tucked its tail.", "Its emotional state is uncertain."
    )
    with patch.object(OpenAIGenerator, "generate", return_value=response) as generate:
        generate.side_effect = AIGenerationError("Test failure") if failed else None
        assert main() == int(failed)
        user_input, context = generate.call_args.args
        assert "dog" in user_input and "Illustrative test context" in context
    output = capsys.readouterr()
    if failed:
        assert "Generation failed: Test failure" in output.err
    else:
        result = json.loads(output.out[output.out.index("{") :])
        assert result == {
            "observations": response.observations,
            "interpretation": response.interpretation,
        }


@pytest.mark.parametrize("missing", ["OPENAI_API_KEY", "OPENAI_MODEL"])
def test_demo_missing_config(missing: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.delenv(missing)
    assert main() == 1

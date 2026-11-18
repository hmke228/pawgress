"""Verify actionable API diagnostics and redaction without live requests."""

import httpx
import pytest
from openai import APIConnectionError, APIError, APITimeoutError, BadRequestError

from pawgress.openai_errors import describe_api_error


@pytest.mark.parametrize("kind", [APIConnectionError, APITimeoutError])
def test_connection_error_category_is_preserved(kind: type[APIConnectionError]) -> None:
    error = kind(request=httpx.Request("POST", "https://example.test/responses"))
    details = describe_api_error(error)
    assert kind.__name__ in details
    assert error.message in details
    assert "HTTP" not in details


def test_status_error_redacts_credentials_and_image_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "environment-secret")
    request = httpx.Request(
        "POST",
        "https://example.test/responses",
        headers={"Authorization": "Bearer request-secret"},
        content=b"PRIVATE REQUEST BODY",
    )
    error = BadRequestError(
        "Do not use the unstructured wrapper",
        response=httpx.Response(
            400, request=request, headers={"x-request-id": "req_test"}
        ),
        body={
            "message": "Bad image: data:image/png;base64,cHJpdmF0ZQ==\n"
            "environment-secret request-secret sk-proj-masked***123\x1b",
            "code": "invalid_image",
            "param": "input[0].content[1]",
        },
    )
    details = describe_api_error(error)
    for expected in (
        "BadRequestError",
        "HTTP 400",
        "Bad image",
        "invalid_image",
        "input[0].content[1]",
        "req_test",
        "[IMAGE REDACTED]",
    ):
        assert expected in details
    for private in (
        "environment-secret",
        "request-secret",
        "sk-proj-",
        "cHJpdmF0ZQ==",
        "PRIVATE REQUEST BODY",
        "\n",
        "\x1b",
        "unstructured wrapper",
    ):
        assert private not in details


@pytest.mark.parametrize("body", [None, "invalid response", {"message": 42}])
def test_error_message_fallback_is_bounded(body: object) -> None:
    error = APIError(
        "Unexpected response " + "x" * 2000,
        httpx.Request("POST", "https://example.test/responses"),
        body=body,
    )
    details = describe_api_error(error)
    assert details.startswith("APIError; Unexpected response")
    assert len(details) == 1500

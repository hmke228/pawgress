"""Readable SDK error details without exposing credentials or embedded images."""

import os
import re

from openai import APIError


def describe_api_error(error: APIError) -> str:
    """Preserve the failure category and provider diagnostics, not request data."""
    details = [type(error).__name__]
    status = getattr(error, "status_code", None)
    if status is not None:
        details.append(f"HTTP {status}")
    message = error.body.get("message") if isinstance(error.body, dict) else None
    details.append(message if isinstance(message, str) else error.message)
    for label, value in (
        ("code", error.code),
        ("parameter", error.param),
        ("request ID", getattr(error, "request_id", None)),
    ):
        if value is not None:
            details.append(f"{label}: {value}")
    text = "; ".join(details)
    for secret in (
        os.getenv("OPENAI_API_KEY"),
        error.request.headers.get("authorization", "").removeprefix("Bearer "),
    ):
        if secret:
            text = text.replace(secret, "[REDACTED]")
    text = re.sub(r"sk-[^\s\"'<>]+", "[REDACTED]", text)
    text = re.sub(r"data:image/[^\s\"'<>]+", "[IMAGE REDACTED]", text)
    return re.sub(r"[\x00-\x1f\x7f]", " ", text)[:1500]

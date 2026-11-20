"""Run both real CLI entry points across separate processes with offline HTTP."""

import json
import sqlite3
import subprocess
import sys
import sysconfig
from contextlib import closing
from pathlib import Path

import pytest
from PIL import Image

SCRIPT = r"""
import json
import os
import runpy
import sys
from unittest.mock import patch
import httpx
from openai import OpenAI

entry, database, fail = sys.argv[1:]
sys.argv = [entry, "--dog", "--db", database]
os.environ["OPENAI_API_KEY"] = "offline-test"
os.environ["OPENAI_MODEL"] = "test-model"
fields = {
    "observations": "Owner reports barking; image shows a lowered tail.",
    "interpretation": "Emotion is uncertain.",
    "scene_context": "Another dog approaching outdoors, as reported by owner.",
    "safety_assessment": "A still image cannot establish safety.",
    "recommendations": "Allow space and observe.",
}
def handle(request):
    if fail == "forbid":
        raise AssertionError("Unexpected API request for invalid image input.")

    body = json.loads(request.content)
    if body["text"]["format"]["name"] == "ai_response":
        content = body["input"][0]["content"]
        assert content[1]["type"] == "input_image"
        assert json.loads(content[0]["text"])["canine_knowledge"]
        result = fields
    else:
        if fail == "yes":
            return httpx.Response(500, json={"error": {"message": "Offline failure"}})
        payload = json.loads(body["input"])
        if "candidates" in payload:
            result = {"relevant_report_ids": [r["report_id"] for r in payload["candidates"]]}
        else:
            history = payload["selected_history"]
            assert len(history) <= 3
            result = {"comparison": "Similar reported cues; stills limit comparison.",
                      "referenced_report_ids": [r["report_id"] for r in history]}
    return httpx.Response(200, json={"status": "completed", "output": [{
        "type": "message", "role": "assistant", "content": [{
            "type": "output_text", "text": json.dumps(result), "annotations": []
        }]
    }]})
with OpenAI(max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(handle))) as client:
    with patch("pawgress.pipeline.OpenAI", return_value=client):
        if entry == "pawgress":
            runpy.run_module(entry, run_name="__main__")
        else:
            runpy.run_path(entry, run_name="__main__")
"""


@pytest.mark.parametrize(
    "entry", ["pawgress", str(Path(sysconfig.get_path("scripts")) / "pawgress")]
)
def test_dog_workflow_across_processes(entry: str, tmp_path: Path) -> None:
    database = tmp_path / "reports.db"
    image = tmp_path / "dog.png"
    with Image.new("RGB", (8, 8), color="blue") as picture:
        picture.save(image, format="PNG")
    reports = []
    for attempt in range(6):
        # Last attempt fails during comparison and must not leave a partial report.
        fail = attempt == 5
        answers = [] if attempt else ["Promise", "Golden dog; usually playful."]
        answers += [
            "" if attempt else "Another dog approached.",
            str(image),
            "done",
            "",
        ]
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                SCRIPT,
                entry,
                str(database),
                "yes" if fail else "no",
            ],
            input="\n".join(answers) + "\n",
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        assert result.returncode == int(fail), result.stderr
        with closing(sqlite3.connect(database)) as connection:
            saved = [
                json.loads(row[0])
                for row in connection.execute(
                    "SELECT payload FROM dog_reports ORDER BY created_at, report_id"
                )
            ]
        assert saved[: len(reports)] == reports
        if fail:
            assert saved == reports
            assert "history filtering request failed" in result.stderr
            assert "HTTP 500" in result.stderr
            assert "Offline failure" in result.stderr
            assert "Pawgress Dog Report" not in result.stdout
            continue
        assert len(saved) == attempt + 1
        current = saved[-1]
        assert (
            current["referenced_report_ids"]
            == [r["report_id"] for r in reversed(reports)][:3]
        )
        assert current["report_id"] in result.stdout
        assert "Recommendations" in result.stdout
        assert (
            "Dog's name:" not in result.stdout
            if attempt
            else "Dog's name:" in result.stdout
        )
        assert result.stderr == ""
        reports = saved


@pytest.mark.parametrize(
    "entry",
    ["pawgress", str(Path(sysconfig.get_path("scripts")) / "pawgress")],
)
def test_invalid_image_makes_no_api_request(
    entry: str,
    tmp_path: Path,
) -> None:
    database = tmp_path / "reports.db"
    image = tmp_path / "corrupt.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")  # Invalid PNG

    answers = [
        "Promise",
        "Golden dog; usually playful.",
        "Another dog approached.",
        str(image),
        "done",
    ]
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            SCRIPT,
            entry,
            str(database),
            "forbid",
        ],
        input="\n".join(answers) + "\n",
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert result.returncode == 1, result.stderr
    assert f"Invalid image '{image}':" in result.stdout
    assert "could not be read or decoded" in result.stdout
    assert "Please provide at least 1 image file(s)." in result.stdout
    assert "Dog report cancelled." in result.stderr
    assert "Traceback" not in result.stderr
    assert "Unexpected API request" not in result.stderr
    assert "Pawgress Dog Report" not in result.stdout

    with closing(sqlite3.connect(database)) as connection:
        count = connection.execute("SELECT COUNT(*) FROM dog_reports").fetchone()[0]
    assert count == 0

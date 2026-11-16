# Epic 2 Manual Testing (macOS / zsh)

## 1. Configure the environment

Run these commands from the repository root:

```zsh
source .venv/bin/activate
read -s "OPENAI_API_KEY?OpenAI API key: "
echo
export OPENAI_API_KEY
read "OPENAI_MODEL?Model ID (vision + Structured Outputs): "
export OPENAI_MODEL
pawgress --help
```

`read -s` hides the key and keeps its value out of command history. Do not share
it in chat, put it in source code, or commit it.
At the Model ID prompt, enter a model available to your account that supports
image inputs, the Responses API, and Structured Outputs. See the official
[image input documentation](https://developers.openai.com/api/docs/guides/images-vision)
and [Structured Outputs documentation](https://developers.openai.com/api/docs/guides/structured-outputs).
The application does not load `.env` automatically. Set the environment variables
again when opening a new terminal.

## 2. Generate the first report

Use a new database file to isolate testing. Keep the same path for subsequent runs:

```zsh
pawgress --dog --db /tmp/pawgress-epic2-manual.db
```

Respond to the prompts:

1. **Dog's name:** For example, `Promise`.
2. **Appearance, basic details, and behavioral background:** Include breed, age,
   color, sex, neuter status, identifying features, and behavioral background.
   These details are currently saved together in one description field. Example:
   `2-year-old female golden retriever, spayed, red collar; usually playful.`
3. **Situation:** Describe what actually happened in the submitted images. Example:
   `At the park, another dog approached Promise. She lowered her body and tucked her tail.`
   This field is required for the first report.
4. **Image Path:** Enter one full image path at a time, with at least one image.
   Enter `done` when finished. Paste paths without quotes or shell escaping;
   paths containing spaces and paths beginning with `~/` are supported.
5. **Target dog:** If several dogs appear, identify yours. Example:
   `The golden dog wearing a red collar`. You may press Enter to skip this prompt.

Use actual PNG, JPEG, or WebP images. HEIC input is not supported. Local validation
checks file signatures only; the API performs image decoding.
The output should include Scene, Safety Assessment, Behavioral Observations,
Interpretation, Comparison, and Recommendations.
The first report should show `No comparable history available.` and
`Referenced reports: None`, along with a unique report ID, UTC timestamp, and
storage path. Check that the report distinguishes owner descriptions from visual
evidence, identifies the correct dog, and does not infer sounds or duration from
still images.

## 3. Generate subsequent reports

```zsh
python -m pawgress --dog --db /tmp/pawgress-epic2-manual.db
```

The saved profile should appear automatically without asking for the dog's basic
information again. You may leave the new situation blank, but images are still
required. Submit images from the same or a behaviorally comparable scene, then
inspect Comparison and Referenced reports.

All historical scenes are filtered before selecting the latest up to three
matches. Use one when only one matches and two when only two match; unrelated
reports must never fill the remaining slots. After generating five reports from
comparable scenes, the fifth should reference at most the three latest matching
reports. It must not reference itself.

Next, submit a clearly different scene and check that unrelated reports are
excluded. If none match, the stored comparison and reference IDs should be
`null` and `[]`. Scene matching depends on model judgment, so live results are
not fixed. Offline tests separately verify handling of zero, one, two, three,
and more than three matches using deterministic responses.

## 4. Inspect complete saved reports

```zsh
python - <<'PY'
import json
import sqlite3
from contextlib import closing
with closing(sqlite3.connect('/tmp/pawgress-epic2-manual.db')) as db:
    rows = db.execute('SELECT payload FROM dog_reports ORDER BY created_at').fetchall()
for (payload,) in rows:
    print(json.dumps(json.loads(payload), ensure_ascii=False, indent=2))
PY
```

Check `behavioral_observations.comparison` and `referenced_report_ids`, and verify
that previous reports have not been overwritten. Each database holds one dog's
profile and history. To repeat the first-run test, choose a new `--db` filename
and retain the old file. Without `--db`, the default path is
`~/.local/share/pawgress/pawgress.db`.

## 5. Test failures and edge cases

- Enter a nonexistent image path: the CLI should prompt again. Duplicate paths
  should not be added twice.
- Submit a plain text file as an image: the CLI should report an image format
  error without generating a report.
- Press Ctrl-D or Ctrl-C: the CLI should exit without a Python traceback.
- Unset the environment variables, then run `pawgress --dog`: the CLI should
  request key/model configuration before collecting input.
- If the API or comparison fails, the exit code should be 1. No partial report
  should be saved, and existing reports should remain unchanged. The profile may
  remain saved for a retry.
- API errors should identify report generation, history filtering, or comparison,
  and show the SDK error category, HTTP status, provider details, and request ID
  when available. Credentials and embedded image data must not appear in errors.
- A missing, malformed, or empty knowledge base should prevent generation. Use
  `--knowledge-base /path/to/references.json` to select a team-maintained collection.

The first report uses one API request. With history but no matching scenes, a run
normally uses two requests. With matching scenes, it normally uses three:
generation, filtering, and comparison. Requests are not retried automatically,
and each has a 30-second timeout setting. Network issues, model permissions,
quota limits, or invalid credentials can cause failures.

Images and the profile are sent in the current-report request. Current and
historical scene descriptions and observations are sent in comparison requests.
The database stores the profile and complete reports, not the image files.
Retain your original photographs separately.

## 6. Current validation scope

All repository tests run offline without using your key. They do not establish
the accuracy of live model judgments. The bundled knowledge base currently has
one professional reference. If the situation is absent or no keywords match,
its general background is used. Retrieval does not infer search terms from
images or reuse an old situation as a new fact. The team still needs to expand
and review reference coverage.

All historical candidates are currently sent to the model in one request, which
suits a small MVP history. Batched filtering for large histories is not implemented.
The legacy `pawgress "text"` command runs the Epic 1 demonstration with mock
history. Use `--dog` for Epic 2 acceptance testing.

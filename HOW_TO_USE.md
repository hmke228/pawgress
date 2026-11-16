# How to Use Pawgress

Pawgress is a terminal application that creates a behavior report for one dog
from your description and photos. Later reports can compare observations with
the same dog's history. You do not need to edit Python files to use it.

## 1. Before you start

You need Python **3.13**, Git (if cloning), an internet connection, an OpenAI API
key, and at least one PNG, JPEG, or WebP photo. HEIC files must be converted first.
Use a model ID available to your account that supports images and Structured
Outputs; ask your team for the model ID if unsure. Live requests may incur charges.
The commands below use **Bash** on macOS, Linux, or Windows through WSL.

## 2. Download and install

Open a terminal and run `bash` so the commands in this guide work consistently.
Download the project with Git:

```bash
git clone https://github.com/hmke228/pawgress.git
cd pawgress
```

If you already downloaded and extracted a ZIP, skip cloning and use `cd` to enter
the extracted folder containing `README.md` and `pyproject.toml`. Then run:

```bash
python3.13 --version
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
pawgress --help
```

The version should be Python 3.13.x, and help should list `--dog`.
SQLite support is included with Python; no database server is needed.

## 3. Configure your API access

Run these commands in the same Bash terminal. Paste your key at the first prompt;
it will not appear on screen or be recorded as a command in shell history.

```bash
read -r -s -p "OpenAI API key: " OPENAI_API_KEY
echo
export OPENAI_API_KEY
read -r -p "Model ID: " OPENAI_MODEL
export OPENAI_MODEL
```

Keep your key private. Pawgress does not automatically read `.env` files.
Your profile and images are sent to OpenAI to generate the report; scene and
observation text from current and historical reports is used for comparison.

## 4. Create your first report

Run `pawgress --dog`, then answer the prompts:

1. **Dog's name:** For example, `Promise`.
2. **Appearance, basic details, and behavioral background:** For example,
   `2-year-old female golden retriever, spayed, red harness; usually playful.`
3. **Situation:** Describe the actual event, such as
   `Another dog approached Promise at the park. She lowered her body.`
4. **Image Path:** Enter a full path to a photo, such as
   `/Users/yourname/Pictures/dog.jpg`. Add more paths one at a time, then enter
   `done`. At least one image is required. Paste paths without quotes or shell
   escaping, even if they contain spaces. Paths beginning with `~/` also work.
5. **Target dog:** If multiple dogs appear, describe yours, such as
   `The golden dog with a red collar`. Otherwise, you may press Enter to skip.

Wait for generation to finish. The report includes **Safety Assessment**,
**Behavioral Observations**, **Interpretation**, **Comparison**, and
**Recommendations**, plus the scene, report ID, timestamp, and storage path.
For a first report, `No comparable history available.` is expected.

## 5. Use Pawgress again

Run `pawgress --dog` again. The profile is reused; the new situation is optional,
but new images are still required. Comparison first filters comparable scenes,
then uses the newest **up to three** matching reports. One or two matches are
enough; unrelated reports never fill the remaining slots. No matches means no comparison.

In a new terminal, enter Bash, return to the project folder, activate `.venv`,
and repeat step 3 before running Pawgress. `python -m pawgress --dog` also works.

## 6. Saved data and separate trials

The default database is `~/.local/share/pawgress/pawgress.db`. It holds one dog's
profile and complete reports; previous reports are not overwritten. Original
photos are not copied into the database. Keep them separately.
For a fresh trial, use `pawgress --dog --db ./trial.db` with a new filename.
Keep using that same path to reuse its profile and history. There is no profile-edit
command yet. See the [manual testing guide](docs/epic2_manual_testing.md) to inspect saved reports.

## 7. Troubleshooting and current limits

| What you see                    | What to do                                                                                                                                                           |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `python3.13: command not found` | Install Python 3.13, then repeat installation.                                                                                                                       |
| `pawgress: command not found`   | Activate `.venv` and run `python -m pip install -e .` again.                                                                                                         |
| Help does not list `--dog`      | Ask your team for the checkout containing the integrated dog workflow.                                                                                               |
| Missing API key or model        | Repeat step 3 in the terminal where you run Pawgress.                                                                                                                |
| Image path or format error      | Use an existing readable PNG, JPEG, or WebP file, without surrounding quotes.                                                                                        |
| OpenAI request failed           | Read the error category, HTTP status, and provider message. Check key/model access for 401/403/404, quota or rate limits for 429, and request/image details for 400. |
| No comparison appears           | There may be no history or no comparable scenes; this is expected.                                                                                                   |

Press Ctrl-C to cancel. A failed generation or comparison does not save a partial
report; the profile may remain saved for a retry. Successful runs use one to
three API requests depending on history. The bundled knowledge base currently
contains only one professional reference, and model interpretations can be wrong.
If a request fails, share the displayed error and request ID with the team, never
your API key. `APITimeoutError` indicates a timeout; `APIConnectionError` indicates
a connection failure. Do not assume every failure is a timeout.
Use `--dog` for this workflow; `pawgress "text"` is the older mock-history demo.
For development setup and automated checks, see [README.md](README.md).

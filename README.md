# LinkedIn AutoPilot

A browser-based LinkedIn inbox worker built with Python, Playwright, and SQLite.

The service monitors incoming connection invitations and conversations. It handles invitations from the received queue and prepares brief, context-aware responses to inbound messages. It never creates connection requests, starts conversations, or sends bulk messages.

## Features

- **Invitation processing** — reads the received-invitations page and accepts pending invitations when enabled.
- **Inbound message handling** — examines existing conversations and acts only on the latest inbound event.
- **Contextual responses** — optional language-model responses based on recent thread context, with an offline fallback.
- **Conversation safety** — rechecks the latest event before composing a send and requires an outbound UI confirmation.
- **Processing state** — SQLite records message fingerprints and handling status to avoid repeating completed work after restarts.
- **Operational controls** — dry-run mode, per-sender allowlist, polling interval, thread cap, and persistent browser profile.
- **Container support** — Docker image with Playwright Chromium, a virtual display, and persistent runtime storage.

## Architecture

```text
LinkedIn browser
    |
    +-- Received invitations --> Invitation handler
    |
    +-- Existing conversations --> Inbound event filter
                                     |
                                     +--> SQLite processing state
                                     |
                                     +--> Reply generator
                                             |
                                             +--> Optional OpenAI API
                                             +--> Deterministic fallback
                                     |
                                     +--> UI send + confirmation
```

## Project files

| Path | Responsibility |
| --- | --- |
| `bot.py` | Browser lifecycle, invitation handling, thread scanning, and send confirmation |
| `replies.py` | Short multilingual message responses and optional contextual generation |
| `storage.py` | Persistent message fingerprints and processing status |
| `tests/` | Automated behavior and persistence tests |
| `requirements.txt` | Pinned Playwright dependency and runtime packages |
| `Dockerfile` | Chromium container image |
| `deploy/entrypoint.sh` | Linux virtual-display startup |
| `.env.example` | Environment configuration template |
| `DEPLOYMENT.md` | Local execution and hosted deployment configuration |
| `SECURITY.md` | Credential handling and access boundaries |
| `SUBMISSION.md` | Competition submission summary |

## Requirements

Python 3.11+, a desktop environment for interactive browser login, and a LinkedIn account under your control. An OpenAI API key is optional. No LinkedIn password or cookie is embedded in the source.

## Run on Windows

Clone the repository and open PowerShell inside its root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
Copy-Item .env.example .env
.\.venv\Scripts\python.exe bot.py
```

Sign in to LinkedIn in the opened Chromium window, then return to the terminal and press Enter. Browser state is retained in the configured profile directory.

The default `DRY_RUN=true` previews detected actions without accepting invitations or sending messages. After validating the browser selectors and reply behavior using accounts you control, set `DRY_RUN=false` to enable actions.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `DRY_RUN` | `true` | Preview without making account changes |
| `POLL_SECONDS` | `5` | Delay between scan cycles, excluding scan duration |
| `MAX_THREADS` | `40` | Maximum conversations scanned per cycle |
| `BASELINE_ON_START` | `true` | Treat existing latest inbound messages as already seen |
| `ALLOWED_SENDER_NAMES` | empty | Optional comma-separated sender allowlist |
| `OPENAI_API_KEY` | empty | Optional private AI API key |
| `OPENAI_MODEL` | `gpt-4.1-mini` | Model for contextual responses |
| `BROWSER_PROFILE_DIR` | `.browser-profile` | Persistent Chromium browser data |
| `STATE_DB_PATH` | `.state/messages.db` | SQLite processing state |
| `UNATTENDED` | `false` | Wait for browser authentication without terminal input |
| `LOGIN_TIMEOUT_SECONDS` | `900` | Authentication timeout for unattended startup |

For the judge's first message, start the worker before the assessment begins. `BASELINE_ON_START=true` skips the latest inbound message already present when the worker first starts. Choose the setting deliberately.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
```

GitHub Actions executes the unit tests on pushes and pull requests. A controlled live test is required to establish compatibility with the current LinkedIn interface.

## Deployment

The container runs Chromium using a virtual display and stores the browser profile and SQLite database on persistent storage. See [DEPLOYMENT.md](DEPLOYMENT.md) for Railway and local execution details.

The remote desktop component is an **internal service**, not a public website. A private authenticated access method must be established before remote login; do not expose its noVNC port to the internet.

## Current limitations

- LinkedIn's page structure can change and require selector updates.
- Attachments are identified but their contents are not read or interpreted.
- Without an AI API key, the fallback cannot answer detailed personal or business questions.
- Uncertain outbound delivery remains flagged for inspection instead of being automatically resent.
- A hosted Chromium session requires secure interactive authentication and sufficient memory; Railway trial resources and uptime are not guaranteed.
- The current code has unit tests, but invitation acceptance and message delivery still require live acceptance tests.

## Account and data handling

Only inbound interactions are eligible for processing. Message bodies are not committed to the repository. Local browser data, environment files, and database state are excluded from version control. Review [SECURITY.md](SECURITY.md) before deployment.

This uses unofficial browser automation; account restrictions are possible under LinkedIn's platform rules.

## Competition

The required profile URL and concise submission note are recorded in [SUBMISSION.md](SUBMISSION.md).

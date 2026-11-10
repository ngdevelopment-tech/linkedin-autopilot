# LinkedIn AutoPilot

Inbound-only browser automation for a timed LinkedIn engineering exercise.

[![Tests](https://github.com/ngdevelopment-tech/linkedin-autopilot/actions/workflows/tests.yml/badge.svg)](https://github.com/ngdevelopment-tech/linkedin-autopilot/actions/workflows/tests.yml)

## Scope

This experimental Python worker opens LinkedIn with Playwright, attempts to accept incoming connection invitations, and responds to inbound messages. It never sends invitations or initiates conversations. SQLite stores processing fingerprints, not message bodies.

**Validation status:** Unit tests are included, but live LinkedIn invitation handling and messaging are **not yet verified**. This project must be tested with a controlled account before competition submission. LinkedIn interface changes and account restrictions can interrupt the worker.

## Project structure

| Path | Purpose |
| --- | --- |
| `bot.py` | Browser worker: invitations, inbound conversations, send confirmation |
| `replies.py` | Contextual replies with optional OpenAI API and offline fallbacks |
| `storage.py` | SQLite processing status and deduplication |
| `tests/` | Unit tests |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Container build |
| `deploy/entrypoint.sh` | Virtual display and private remote browser processes |
| `.env.example` | Non-secret configuration template |
| `DEPLOYMENT.md` | Windows and cloud setup instructions |
| `SECURITY.md` | Secret handling and browser-access requirements |
| `SUBMISSION.md` | Competition note |

## Windows setup

From the repository root, in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
Copy-Item .env.example .env
.\.venv\Scripts\python.exe bot.py
```

Log into LinkedIn manually in the Chromium window and press Enter. The default `DRY_RUN=true` prevents actual invitation acceptance or message sending until you explicitly disable it. Test with accounts you control.

## Configuration

| Name | Default | Description |
| --- | --- | --- |
| `DRY_RUN` | `true` | Preview activity without clicking Accept or sending replies |
| `POLL_SECONDS` | `5` | Delay between full scan cycles; total latency is longer |
| `MAX_THREADS` | `40` | Maximum number of visible conversations examined per cycle |
| `BASELINE_ON_START` | `true` | Skip already visible inbound messages at first launch |
| `ALLOWED_SENDER_NAMES` | blank | Restrict to displayed sender names |
| `OPENAI_API_KEY` | blank | Optional AI-generated reply service; keep private |
| `OPENAI_MODEL` | `gpt-4.1-mini` | API model when a key is configured |
| `BROWSER_PROFILE_DIR` | `.browser-profile` | Browser session path |
| `STATE_DB_PATH` | `.state/messages.db` | Deduplication database |
| `UNATTENDED` | `false` | Wait for browser login instead of terminal prompt |
| `LOGIN_TIMEOUT_SECONDS` | `900` | Unattended sign-in timeout in seconds |

## Running tests

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
```

Automated tests verify isolated code behavior and do not establish that LinkedIn DOM selectors or message delivery work. Validate the invitation path, incoming text, consecutive messages, attachments, restarts, and send confirmation in a real browser before submission.

## Deployment limitations

The Docker image supports a visible browser under a virtual display. Its internal noVNC endpoint has **no authentication**. **Never publish port 6080 or attach a public Railway domain to it.** Remote login cannot be completed securely on Railway without an additional private authentication/access mechanism. The Railway service should remain private and in dry-run mode until this is implemented.

A continuously running cloud container may exceed Railway's trial resource quotas. See [DEPLOYMENT.md](DEPLOYMENT.md) for setup and limitations, [SECURITY.md](SECURITY.md) for security, and [SUBMISSION.md](SUBMISSION.md) for the competition note.

This unofficial browser automation may violate LinkedIn's policies or result in account restrictions.

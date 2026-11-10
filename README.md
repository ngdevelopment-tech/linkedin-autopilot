# LinkedIn AutoPilot

Python automation service for inbound LinkedIn connection requests and direct messages.

## Features

- Reviews the incoming invitation queue and accepts pending requests.
- Monitors existing message conversations and responds only to inbound messages.
- Generates concise contextual replies using a configurable language-model provider; deterministic fallback responses are available.
- Tracks message-processing fingerprints in SQLite to avoid repeating completed operations.
- Rechecks conversation state before sending and verifies outbound messages where possible.
- Supports dry-run mode, sender allowlists, restart persistence, and adjustable scanning.
- Runs locally with Playwright Chromium or in a Linux container.

## Architecture

```text
Playwright browser
  ├── Incoming invitations → Invitation handler
  └── Existing conversations → Inbound event filter
                                ├── SQLite processing state
                                ├── Reply engine
                                └── Send and UI confirmation
```

## Repository structure

| Path | Description |
| --- | --- |
| `bot.py` | Browser lifecycle, invitations, conversations, and message handling |
| `replies.py` | Message-response strategy and fallback behavior |
| `storage.py` | Persistent message fingerprints and processing states |
| `tests/` | Unit tests for response behavior and persistence |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Playwright browser container |
| `deploy/entrypoint.sh` | Container display startup |
| `.env.example` | Configuration reference |
| `DEPLOYMENT.md` | Runtime configuration and infrastructure |
| `SECURITY.md` | Private data and access controls |

## Requirements

- Python 3.11 or newer
- Chromium installed through Playwright
- A LinkedIn account with access to incoming invitations and messages
- Optional response-generation API credential

## Windows installation

Open PowerShell in the repository directory:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
Copy-Item .env.example .env
.\.venv\Scripts\python.exe bot.py
```

Sign in using the Chromium browser window and return to PowerShell. Press Enter after the LinkedIn feed is visible. The session is kept in the configured browser profile directory.

The default `DRY_RUN=true` logs proposed actions without modifying the account. To enable actual invitation acceptance and message sending, change it to `false` after checking the browser selectors.

## Configuration

| Setting | Default | Description |
| --- | --- | --- |
| `DRY_RUN` | `true` | Preview actions without sending or accepting |
| `POLL_SECONDS` | `5` | Delay after a complete scan |
| `MAX_THREADS` | `40` | Conversations examined per scan |
| `BASELINE_ON_START` | `true` | Register existing inbound messages as previously seen |
| `ALLOWED_SENDER_NAMES` | empty | Optional comma-separated sender restriction |
| `OPENAI_API_KEY` | empty | Optional reply-engine API credential |
| `OPENAI_MODEL` | `gpt-4.1-mini` | Model used when the external response service is configured |
| `BROWSER_PROFILE_DIR` | `.browser-profile` | Persistent browser profile |
| `STATE_DB_PATH` | `.state/messages.db` | SQLite database location |
| `UNATTENDED` | `false` | Browser sign-in without waiting for terminal input |
| `LOGIN_TIMEOUT_SECONDS` | `900` | Unattended browser sign-in deadline |

The full scan includes navigation through conversations and may take longer than `POLL_SECONDS`. Set `BASELINE_ON_START` intentionally: existing inbound messages present during the initial scan are marked as seen when enabled.

## Processing sequence

1. Open the received-invitations page and process pending invitations.
2. Inspect conversation entries in the message inbox.
3. Skip conversations with no eligible inbound message.
4. Check persistent state to avoid processing the same inbound event twice.
5. Generate a short reply from the inbound message and recent conversation history.
6. Recheck the conversation before sending.
7. Send and look for an outbound UI confirmation.
8. Record confirmed, pending, or preview processing status and repeat.

## Response behavior

| Incoming input | Offline fallback response |
| --- | --- |
| `hello` | Hey! Good to hear from you. How's it going? |
| `🙂` | Hey 😊 What's up? |
| `مرحبا` | أهلاً! كيف فيني ساعدك؟ |
| `bonjour` | Salut ! Comment puis-je t'aider ? |
| `https://example.org` | Thanks for the link. What would you like me to focus on? |
| File or image without text | Thanks for sending this. What would you like me to look at? |
| Unknown question | Good question. Could you share a little more context? |

With the optional reply service configured, replies can use recent conversation context. The fallback is deliberately generic and should not be used as evidence of sophisticated semantic understanding.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
```

The CI workflow runs syntax compilation and unit tests. Browser integration checks require a signed-in browser and controlled inbound test messages.

## Operational limitations

- LinkedIn interface changes can invalidate selectors.
- File and image contents are not interpreted.
- Unconfirmed sends are retained as pending rather than blindly repeated.
- Offline responses do not provide factual answers about the account holder.
- Hosted browser login requires an authenticated private access method; the container's remote-desktop port must not be publicly exposed.
- Chromium consumes memory and CPU, which may exceed small hosting allocations.

See [DEPLOYMENT.md](DEPLOYMENT.md) and [SECURITY.md](SECURITY.md) for infrastructure and private-data handling.

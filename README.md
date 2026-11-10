# LinkedIn AutoPilot
### Inbound LinkedIn automation • Playwright • Python • SQLite • Railway

I built **LinkedIn AutoPilot** to handle incoming connection invitations and respond to incoming LinkedIn messages on my own account, while never initiating conversations or sending connection requests. The challenge is not simply clicking Send: it is understanding the latest inbound message, speaking naturally, staying within the facts I can verify, and avoiding duplicate responses after a timeout or restart.

**My LinkedIn:** https://www.linkedin.com/in/naim-gerges-892591271/  
**My portfolio:** https://ngdevelopment-tech.github.io/naimgerges/  
**Deployment:** Railway, connected to this repository's `main` branch.

> **Status and honesty:** The code and offline tests demonstrate message policy, reply fallbacks and persistence. LinkedIn browser selectors and end-to-end sending are integration-dependent and must be validated against a signed-in account. The current hosted deployment is in `DRY_RUN=true` until safe detection is verified. No test run is a guarantee of uninterrupted uptime or delivery.

## Features

- **Inbound only:** never sends invitations, starts a DM or bulk-messages contacts.
- **Connection requests:** reviews and accepts received invitations when live mode is explicitly enabled.
- **Messages:** checks recent conversations, filters for confirmed inbound messages, and replies using recent thread context.
- **Human tone:** short first-person responses as Naim, without pretending to know unpublished personal facts.
- **Unusual inputs:** short/empty texts, emojis, Arabic, French, Spanish, long messages, links, attachments, rude messages and unverifiable questions.
- **Two reply modes:** optional OpenAI-powered conversational replies; offline deterministic fallback if no API key is configured or the provider fails.
- **Safety:** per-inbound-message atomic SQLite claims, durable across restarts; never automatically resend a message after an uncertain Send result.
- **Operations:** `DRY_RUN` by default, optional sender allowlist for tests, persistent signed-in browser profile, bounded scans, low-memory headless mode and CI tests.

## How it works

```text
                      LinkedIn (signed-in Chromium)
                                 |
                      +----------+----------+
                      |                     |
              Received invitations    Messaging inbox
                      |                     |
              Accept (if live)       Load conversation
                                            |
                                   Identify latest author
                                     /            \
                                Not inbound      Inbound
                                   |                |
                                  Skip      Stable event identity
                                                    |
                                          SQLite atomic claim
                                                    |
                                           Contextual reply
                                           (AI or fallback)
                                                    |
                                            Send + verify
                                                    |
                                          Done / uncertain
```

If the direction is unknown, the bot skips that event. If LinkedIn exposes no native event ID, a deterministic visible-history signature is used; that fallback is weaker than a platform event ID and is documented in the limitations.

## Quick start (Windows PowerShell)

```powershell
git clone https://github.com/ngdevelopment-tech/linkedin-autopilot.git
cd linkedin-autopilot
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
Copy-Item .env.example .env
.\.venv\Scripts\python.exe bot.py
```

The first run opens a Chromium window. I sign in directly on LinkedIn, return to PowerShell and press Enter when the inbox is available. No LinkedIn password belongs in `.env` or source code. The browser profile stays on disk for the next run.

**Run locally on macOS/Linux:**

```bash
git clone https://github.com/ngdevelopment-tech/linkedin-autopilot.git
cd linkedin-autopilot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
python bot.py
```

The default `DRY_RUN=true` previews detected events without accepting invitations or sending messages. Keep it enabled while validating selectors. Set `DRY_RUN=false` only after verifying live account behavior. **Do not start two workers using the same browser profile.**

## Run the tests

```bash
python -m pip install -r requirements.txt pytest
python -m compileall -q bot.py replies.py storage.py message_policy.py
python -m pytest -q
```

GitHub Actions runs Python compilation, shell syntax validation, and the unit tests on each push and pull request. Tests cover outbound/inbound gating, repeated text, distinct messages in a thread, cross-thread deduplication, restart persistence and unusual-language reply fallbacks. They do **not** log in to LinkedIn or send test messages.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `DRY_RUN` | `true` | Preview only; never send or accept |
| `OPENAI_API_KEY` | empty | Enables AI replies; no key means local fallback |
| `OPENAI_MODEL` | `gpt-4.1-mini` | Model for contextual replies |
| `ALLOWED_SENDER_NAMES` | empty | Optional exact-name allowlist for controlled tests |
| `POLL_SECONDS` | `5` | Delay after each scanning cycle |
| `MAX_THREADS` | `40` | Upper bound of inbox conversations per cycle |
| `BASELINE_ON_START` | `true` | Skip previously present inbound items on startup |
| `BROWSER_HEADLESS` | `false` | Use non-graphical Chromium after login is saved |
| `UNATTENDED` | `false` | Run without terminal login confirmation |
| `BROWSER_PROFILE_DIR` | `.browser-profile` | Persistent login profile |
| `STATE_DB_PATH` | `.state/messages.db` | Durable event claims |
| `LOGIN_TIMEOUT_SECONDS` | `900` | Authentication wait period |

I use a dedicated Railway volume at `/data` for the Chromium profile and SQLite state, and turn on headless mode for lower runtime overhead. See [DEPLOYMENT.md](DEPLOYMENT.md) for the infrastructure, privacy setup, and recovery process.

## Project files

| File | Responsibility |
| --- | --- |
| `bot.py` | Browser, inbox and invitation handling, send confirmation |
| `message_policy.py` | Incoming-only gate and event identities |
| `replies.py` | Naim's reply voice, optional AI and fallback |
| `storage.py` | SQLite atomic per-message claims |
| `tests/` | Reproducible offline behavior tests |
| `deploy/entrypoint.sh` | Railway headless/graphical service startup |
| `Dockerfile` | Playwright container with OS dependencies |
| `.env.example` | Safe copyable configuration |
| `DEPLOYMENT.md` | Railway deployment and troubleshooting |
| `SUBMISSION.md` | Concise challenge submission note |
| `SECURITY.md` | Credential, privacy and operational boundaries |

## Known limitations

- LinkedIn can change its DOM, virtualize messages or challenge a signed-in browser. Author detection and sending require real-account validation.
- A visible-history event signature can change if LinkedIn reloads or reorders older events; the safest response to ambiguity is to skip, not to retry.
- An uncertain Send is kept as `pending`; the bot does not automatically retry it. This prevents duplicate attempts but may miss a reply.
- Messages with attachments can be acknowledged, but the bot does **not** inspect file or image contents.
- The optional AI key is not included; without it, the local response engine cannot provide arbitrary deep semantic reasoning.
- Chromium can exceed 512 MB RAM on demanding LinkedIn pages; the Railway Trial Plan may therefore not provide reliable continuous service.
- UI selectors for received invitations and messages may require updates. This is a technical prototype using browser automation, not an official LinkedIn API integration.

**Built by Naim Gerges.** See [SUBMISSION.md](SUBMISSION.md) for the challenge-specific note.

# Railway deployment

This is how I run **LinkedIn AutoPilot** on Railway while keeping my browser login and message-processing state between deployments.

## Architecture

```text
GitHub: ngdevelopment-tech/linkedin-autopilot (main)
                    |
             Railway auto-deploy
                    |
           linkedin-worker service
              Playwright Chromium
                    |
   /data/browser                 /data/state/messages.db
   persistent login             persistent message claims
                    |
              LinkedIn inbox
```

- **Project:** LinkedIn AutoPilot (Railway).
- **Service:** `linkedin-worker`, one replica; GitHub source: `main`.
- **Runtime:** Dockerfile-based Playwright Python container.
- **Persistent volume:** 500 MB, mounted at `/data`.
- **Profile:** `/data/browser`.
- **SQLite:** `/data/state/messages.db`.
- **Trial plan:** resource-limited. The headless browser does not guarantee staying below 0.5 GB RAM.
- **Health endpoint:** `/healthz` responds when the HTTP container is booted, not when LinkedIn is authenticated or messages are processing.
- **Public endpoint:** Railway service HTTPS domain for health checks. No LinkedIn credentials or inbox contents are exposed through it.

## Deploy my repository

1. Fork or clone the repo to a GitHub account.
2. In Railway, create a project and connect the GitHub repository. Choose the `main` branch and Dockerfile builder.
3. Attach a persistent volume mounted at `/data`; **do not delete it during redeploys**.
4. Set environment variables in Railway Variables. Never commit a real `.env` file or login cookie.
5. Deploy, inspect GitHub Actions and Railway deployment logs.
6. Authenticate the Chromium browser once using a secure temporary interactive display before enabling `BROWSER_HEADLESS=true`.
7. Confirm `[session] Authenticated LinkedIn navigation confirmed`, followed by `[inbox] pass ...`. For real sends, additionally require evidence that a **new** message was detected and that a send was confirmed in LinkedIn.

### Environment variables

```dotenv
BROWSER_PROFILE_DIR=/data/browser
STATE_DB_PATH=/data/state/messages.db
UNATTENDED=true
BROWSER_HEADLESS=true
DRY_RUN=true
BASELINE_ON_START=true
POLL_SECONDS=12
MAX_THREADS=10
ALLOWED_SENDER_NAMES=
PORT=8080
```

Optional: `OPENAI_API_KEY` and `OPENAI_MODEL`. A configured key enables context-aware AI replies. Without it, the service uses offline keyword/pattern responses. The configured key, if present, must remain a Railway secret; it is never included in the public repo.

### Sign-in procedure

The browser profile persists under `/data/browser`; the worker does not store the LinkedIn password in environment variables.

When using graphical mode for initial login, set `BROWSER_HEADLESS=false`. If `BROWSER_ACCESS_PASSWORD` is configured, the startup script makes a password-protected noVNC display available through the Railway HTTPS domain at `/vnc.html?autoconnect=true&path=websockify`. Sign in to LinkedIn **inside** that browser session. After login, switch back to headless and redeploy.

For headless mode, the deployment uses a small nginx server for `/healthz` and deliberately does **not** start Xvfb, Fluxbox, x11vnc or websockify. The graphical remote desktop is unavailable in this mode. Remove public browser access credentials and disable graphical mode after setup.

### Confirm service health

Expected sequence in Railway deployment logs:

```text
[startup] headless mode: no Xvfb, desktop manager or VNC processes
Inbound LinkedIn worker starting: headless=True
DRY_RUN enabled: no invitations accepted or messages sent
[session] Authenticated LinkedIn navigation confirmed
[inbox] pass baseline=False conversation_count=...
```

A successful Docker deployment does not mean the bot is replying. `DRY_RUN=true` is intentionally non-sending. For a safe controlled test, monitor an **incoming** message and check the persistent claim, the Send action, and actual received LinkedIn message. UI confirmation can fail even when LinkedIn delivers, so never automatically retry uncertain sends.

## Failure modes and safe recovery

| Symptom | Likely cause / next step |
| --- | --- |
| `Aw, Snap!` / crashed tab | Chromium memory pressure. Lower scan size, reduce browser navigation, or use a host with more RAM. |
| `direction=unknown` | LinkedIn's message DOM doesn't prove authorship. **Do not enable live sending.** |
| No stable event ID | The worker uses a local visible-history signature. Avoid retries after errors; inspect conversation. |
| `conversation_count=0` | Inbox loading or selectors changed; inspect page state rather than sending. |
| `Unconfirmed send` | Message may already have been delivered. **Do not reset the pending event claim automatically.** |
| Expired LinkedIn sign-in | Temporarily enable graphical access and reauthenticate using the same persistent profile. |
| Memory near plan limit | Service may restart; measure using Railway Metrics, not assumptions. |

One instance per profile. Protect the Railway Variables and mounted volume. See [SECURITY.md](SECURITY.md).

## Local verification

Use a fresh Python virtual environment. See [README.md](README.md) for complete Windows/macOS/Linux commands and `python -m pytest -q`. A reviewer can run all offline unit tests without LinkedIn credentials, an AI key, or a Railway account.

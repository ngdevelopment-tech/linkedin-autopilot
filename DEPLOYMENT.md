# Deployment guide

## Reality of continuous hosting

The worker needs a continuously running browser session while the competition is being tested. GitHub hosts the source and runs code tests; it does not provide an always-on browser process. Railway can run a container, but trial memory limits, pricing, and availability are plan-dependent. A Playwright Chromium process may exceed trial resources.

## Railway (project created, live login NOT configured)

An existing private Railway project named `linkedin-autopilot` contains a service `linkedin-worker` and a 500 MB persistent volume mounted at `/data`. The service must be linked to this repository. The Dockerfile uses the official Playwright Python image and runs a visible Chromium browser under Xvfb.

**Security requirement:** The container's noVNC endpoint on port 6080 is currently unauthenticated and MUST NOT be exposed using a public Railway domain. It was included only as a starting point for a private login route. Never generate a public domain or expose TCP port 6080 in this state. Railway does not supply an ordinary inbound SSH tunnel like a VPS. This deployment remains blocked until a private, authenticated login strategy is implemented and tested.

The service should mount `/data` and use these variables, entered into Railway's private variables UI:

```text
BROWSER_PROFILE_DIR=/data/browser
STATE_DB_PATH=/data/state/messages.db
UNATTENDED=true
DRY_RUN=true
BASELINE_ON_START=true
POLL_SECONDS=5
```

OpenAI API keys are optional and must be set only through private environment variables. Never paste credentials into project files, GitHub Actions or support chats. Disable DRY_RUN only after inspecting live invitation and messaging behavior.

## Local Windows run (recommended for initial verification)

1. Install Python 3.11 or newer.
2. Extract or clone the repository and open a terminal in its root directory.
3. Run `py -m venv .venv`.
4. Run `.venv\\Scripts\\python.exe -m pip install -r requirements.txt`.
5. Run `.venv\\Scripts\\python.exe -m playwright install chromium`.
6. Copy `.env.example` to `.env`; keep `DRY_RUN=true` initially.
7. Run `.venv\\Scripts\\python.exe bot.py`.
8. Log into LinkedIn manually in Chromium and press Enter in the terminal.
9. Test with an account you control, then enable sending only if the user interface and safety checks work.

## Before competition submission

Test acceptance, a first inbound DM, multiple follow-up DMs, a restart, and attachment/unknown-message handling. Observe actual send confirmations and inspect logs. Keep the runtime online until the competition status confirms that testing is finished. Verify with the organizers that cloud-hosted execution is allowed: their instructions describe running the bot on your own computer.

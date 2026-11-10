# Deployment

## Local runtime

The worker uses a persistent Playwright Chromium profile and a SQLite database. Both paths must be writable. Run a single worker instance per LinkedIn session.

Windows setup and configuration are documented in [README.md](README.md).

## Container runtime

The Docker image uses the official Playwright Python base, installs display services, and runs Chromium with a persistent profile.

Required environment:

```text
BROWSER_PROFILE_DIR=/data/browser
STATE_DB_PATH=/data/state/messages.db
UNATTENDED=true
DRY_RUN=true
BASELINE_ON_START=true
POLL_SECONDS=5
```

Mount persistent storage at `/data`. Keep account credentials and API keys in the hosting provider's private environment configuration. Do not commit runtime data.

## Railway

The service `linkedin-worker` is configured in project `linkedin-autopilot`, with a 500 MB persistent volume mounted at `/data`. Its source is the repository's `main` branch.

The container intentionally exposes no browser-login endpoint. Configure an authenticated private access method before remote sign-in. Railway containers do not provide standard inbound SSH tunnels.

The browser worker requires a valid signed-in session before unattended processing can run. A local interactive run is the simplest approach for validating selectors.

## Health and troubleshooting

Inspect container build and runtime logs for dependency errors, sign-in expiry, selector mismatches, and Chromium memory pressure. A successful container start alone does not demonstrate successful invitation or message processing.

For outbound-send uncertainty, inspect the conversation before resetting a `pending` fingerprint. Avoid starting two instances with the same profile.

## Resource requirements

Browser memory consumption varies with the site and number of conversations. Test container memory before relying on small free-tier plans. A worker only runs while the host is online and its deployment remains active.

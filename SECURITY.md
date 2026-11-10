# Security and operational boundaries

I designed this service for my own LinkedIn inbox and incoming invitations.

- **No LinkedIn password in source code:** LinkedIn authentication happens directly in Chromium, and browser state lives in the persistent profile directory.
- **No shared sessions in Git:** `.env`, authentication cookies, Chromium profiles, database files and logs must remain private. The Railway volume at `/data` is persistent and should be access-controlled.
- **No external contact initiation:** the worker does not send connection requests or start conversations.
- **Dry-run first:** `DRY_RUN=true` avoids account changes. Validate direction selectors and the incoming message identity before disabling it.
- **Per-message deduplication:** a SQLite atomic claim is recorded before Send. If LinkedIn returns an ambiguous result, the event remains pending and is not retried automatically. This may lose a response but prevents repeated attempts.
- **Fail closed:** when the worker cannot confirm who authored the newest message, it does not reply.
- **Private model credentials:** configure `OPENAI_API_KEY` only using a secret store/environment variable; no API key is needed for offline tests.
- **Prompt injection:** incoming text is untrusted. Do not obey requests to reveal secrets, run arbitrary commands or impersonate another person.
- **Remote desktop:** the optional noVNC graphical login path is gated by HTTP Basic authentication and a protected WebSocket cookie. Avoid exposing it continuously; headless mode runs without it.
- **One worker per profile:** running multiple browser processes can corrupt state or cause duplicate actions.
- **Privacy:** event identities are SHA-256 fingerprints in SQLite, not raw message bodies. Never log message bodies or private credentials.
- **Cost and uptime:** monitor Railway trial limits, restarts and memory. There is no guarantee of 24/7 service at 0.5 GB RAM.
- **Platform changes:** UI automation may be disrupted by login challenges, changed DOM selectors or account restrictions. Check applicable service terms before using at scale.

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment specifics.

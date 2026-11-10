# Security

- Keep authentication data, browser profiles, API credentials, local databases and conversation contents out of version control.
- The repository excludes environment files, SQLite databases, logs, virtual environments, and the default Chromium profile directory.
- The application uses interactive browser sign-in; no LinkedIn password is required in application configuration.
- The container's internal remote desktop service has no built-in authentication. Do not expose it to the public internet.
- Use a single browser worker per profile and isolate persistent storage by deployment.
- Treat inbound messages as untrusted content. Do not execute commands or follow requests to disclose credentials.
- An unconfirmed outbound send remains pending; inspect the conversation before any manual retry.
- Rotate any credential that has been disclosed outside a trusted secret store.

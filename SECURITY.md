# Security notes

- Never commit personal access tokens, OpenAI API keys, LinkedIn credentials, cookies, screenshots of conversations, browser profiles, runtime databases, or real message contents.
- The source repository is public; treat all committed content as world-readable.
- `.env`, `.browser-profile`, `.state`, SQLite files, and common log files are excluded by `.gitignore`.
- Browser login is manual. The application does not request or store the LinkedIn password itself; Chromium maintains a browser profile on local or privately mounted storage.
- The current Railway noVNC endpoint is **not authenticated** and MUST NOT be publicly exposed. Private access must be implemented before remote login.
- If a send cannot be confirmed in the UI, the message is left `pending` rather than resent. Inspect it manually.
- Rotate any previously shared tokens before using this project.
- Only test with accounts you own or have permission to use.

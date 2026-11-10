# Competition submission

**Public source:** https://github.com/ngdevelopment-tech/linkedin-autopilot

**LinkedIn profile:** https://www.linkedin.com/in/naim-gerges-892591271/

## Description

A Python browser worker that checks incoming connection invitations and inbound LinkedIn conversations. It attempts to accept invitations and reply briefly in context. Message fingerprints are stored locally to reduce duplicate processing. Messages are never sent proactively.

## Running it

See [README.md](README.md) for local setup and [DEPLOYMENT.md](DEPLOYMENT.md) for cloud deployment considerations. A real browser login is required, and the worker must remain online until the assessment concludes.

## Current limitations

- Browser selectors depend on LinkedIn's current interface and require live verification.
- Message sending uses UI confirmation; ambiguous sends remain pending instead of automatically retrying.
- Media is recognized only as an attachment indicator; files and images are not interpreted.
- Replies use an optional AI service; without its key, answers are basic fallbacks.
- A remote Railway session needs a secure, private login path before unattended use.
- Railway trial resource limits, uptime and LinkedIn access are not guaranteed.
- This implementation is unofficial and may conflict with LinkedIn terms.

**Do not claim the live test has passed until it has actually been run.**

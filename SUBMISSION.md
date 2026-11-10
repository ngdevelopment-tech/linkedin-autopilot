# Technical summary

**Repository:** https://github.com/ngdevelopment-tech/linkedin-autopilot

**LinkedIn profile:** https://www.linkedin.com/in/naim-gerges-892591271/

## Functionality

The service monitors received connection invitations and existing LinkedIn message threads. It accepts incoming invitations and responds to the latest eligible inbound message with a concise reply. Processing fingerprints and status are retained in SQLite to reduce duplicate handling. It does not initiate conversations, send connection invitations or perform bulk messaging.

## Installation

Install Python 3.11+, run `pip install -r requirements.txt`, install Playwright Chromium with `python -m playwright install chromium`, copy `.env.example` to `.env`, and start `python bot.py`. Complete LinkedIn sign-in in the Chromium window. Configure `DRY_RUN=false` to enable account-changing actions after validating selectors.

## Limitations

The browser integration depends on LinkedIn's current interface. Attachments are detected without parsing their contents. Unconfirmed sends require inspection. The optional external response engine is needed for more specific conversational replies. Hosted use requires secure interactive browser sign-in and sufficient resources.

Detailed settings and architecture are documented in [README.md](README.md).

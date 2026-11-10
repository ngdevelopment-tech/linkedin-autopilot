# My challenge note — LinkedIn AutoPilot

**Naim Gerges**  
[LinkedIn](https://www.linkedin.com/in/naim-gerges-892591271/) · [Portfolio](https://ngdevelopment-tech.github.io/naimgerges/) · [Source](https://github.com/ngdevelopment-tech/linkedin-autopilot)

## Short note for the submission form

I built an inbound-only LinkedIn worker using Python, Playwright and SQLite. It checks received connection requests and messages, avoids initiating conversations, and uses persistent event claims to reduce duplicate replies. I deployed it to Railway with a saved browser profile and database on a persistent volume, and added GitHub Actions tests.

To run it: install `requirements.txt`, install Playwright Chromium, copy `.env.template` to `.env`, then run `python bot.py` and sign in through the browser. Start with `DRY_RUN=true`; switch to live mode only after verifying the account and message selectors.

The reply engine supports an optional model API for context-aware answers and a local fallback for common messages. Limitations include LinkedIn interface changes, restricted hosting memory, no attachment-content analysis, and uncertain-send cases that require inspection. Live message delivery and invitation handling need to be validated before enabling production operation.

## How I approached the brief

The assignment asked for quick incoming connection acceptance and natural replies to LinkedIn messages. I wanted to show more than a successful browser click. Even on a small practical task, I think about the complete process: how it runs, what happens when something breaks, whether the result is safe, and how another developer can verify the work.

I chose Python and Playwright for the browser worker, SQLite for persistent message claims, GitHub Actions for automated checks and **Railway for cloud deployment**. I connected Railway directly to the repository and saved the signed-in Chromium profile on a persistent volume, so the service could restart without losing the login.

I also ran a real cross-account LinkedIn test. It confirmed that messages could be delivered, but it revealed duplicate replies and unreliable send confirmation. I didn't treat that as a successful final result: I traced the problem through the message parser and delivery flow, changed deduplication from per-conversation to per-inbound-event claims, and added tests for retries and restarts.

The message reader now checks authorship, preserves native event identities where available and skips messages it cannot safely classify. The reply engine can use a contextual model grounded in my public work, with a limited offline fallback for common situations. I do not claim to read attachments I haven't opened or know personal details I haven't supplied.

## What I wanted to demonstrate

- **Practical engineering:** deliver a deployable worker, not just source code.
- **Understanding the failure modes:** handle browser crashes, session persistence, changing selectors and duplicate sends.
- **Ownership of quality:** keep dry-run controls, tests, logs and honest limitations.
- **Speed with judgment:** work quickly without hiding errors or shipping potentially repeated messages.
- **Clarity for reviewers:** provide local setup, an offline reply showcase, a system diagram, deployment notes, a real troubleshooting record and a roadmap.

I take even short assignments seriously. My goal is to make something I understand end to end and can defend technically, not merely complete a checklist.

## How to inspect it

```bash
git clone https://github.com/ngdevelopment-tech/linkedin-autopilot.git
cd linkedin-autopilot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python demo.py
python -m pytest -q
```

That is an **offline review**. For an actual LinkedIn integration test, follow [README.md](README.md) and [DEPLOYMENT.md](DEPLOYMENT.md) to configure an authenticated Chromium session. The `.env.template` file contains no credentials.

## Verification status

- GitHub Actions has passed **offline tests** as well as syntax and packaging checks.
- The Railway worker has authenticated with LinkedIn and discovered inbound and outbound message events.
- The earlier live test delivered messages but exposed duplicate-send behavior; this was the reason for the persistent event-claim redesign.
- The current deployment remains in `DRY_RUN=true` pending a clean live replay and invitation-acceptance test.
- Model-based replies need a private `OPENAI_API_KEY`. Running without that key uses the local response rules.
- The free Railway trial is memory-constrained, and long-term 0.5 GB stability has **not** been established.

I included these points because I think explaining what works, what failed and what remains to prove is part of doing a technical assignment properly.

**More detail:** [Engineering notes](ENGINEERING_NOTES.md) · [Roadmap](ROADMAP.md) · [Security](SECURITY.md)

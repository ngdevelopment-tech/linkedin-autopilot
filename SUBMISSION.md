# My challenge note — LinkedIn AutoPilot

**Naim Gerges**  
[LinkedIn](https://www.linkedin.com/in/naim-gerges-892591271/) · [Portfolio](https://ngdevelopment-tech.github.io/naimgerges/) · [Source](https://github.com/ngdevelopment-tech/linkedin-autopilot)

## Short note for the submission form

I built an inbound-only LinkedIn worker using Python, Playwright and SQLite. It automatically accepts received connection requests and replies to incoming messages, without initiating conversations or sending invitations. I deployed it on Railway with a persistent browser profile and SQLite event tracking. GitHub Actions checks the code, and a controlled live test confirmed a sent reply and an accepted incoming invitation.

To run it: install `requirements.txt`, install Playwright Chromium, copy `.env.template` to `.env`, then run `python bot.py` and sign in through the browser. Start with `DRY_RUN=true`; switch to live mode only after verifying the account and message selectors.

The worker currently uses concise, rule-based replies; a model API is optional. It can respond to common messages in several languages, but it does not read attachments, and unfamiliar questions may receive a follow-up rather than a detailed answer. The browser depends on LinkedIn's interface and Railway's available memory.

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
- An early duplicate-send issue led me to add persistent per-event claims. The updated worker then delivered one confirmed reply without repeating it in subsequent scans.
- Railway recorded one automatically accepted incoming request. The worker runs with `DRY_RUN=false`, no sender-name restriction and a completed 17-conversation baseline.
- The hosted bot runs without an AI API key, using local response rules. An optional private `OPENAI_API_KEY` enables more contextual replies.
- Railway is running the worker on its resource-limited trial plan; browser memory and LinkedIn UI changes are the main operational considerations.

I included these points because I think explaining what works, what failed and what remains to prove is part of doing a technical assignment properly.

**More detail:** [Engineering notes](ENGINEERING_NOTES.md) · [Roadmap](ROADMAP.md) · [Security](SECURITY.md)

# Challenge submission — LinkedIn AutoPilot

**Built by Naim Gerges**

- **Code:** https://github.com/ngdevelopment-tech/linkedin-autopilot
- **LinkedIn:** https://www.linkedin.com/in/naim-gerges-892591271/
- **Portfolio:** https://ngdevelopment-tech.github.io/naimgerges/
- **Hosting:** Railway, connected to my GitHub `main` branch, running a persistent Playwright Chromium worker with a dedicated SQLite volume.

## My approach

I built a small but practical event-driven browser worker for a difficult target: LinkedIn messages are not a stable public inbox API. I focused on *inbound-only activity*, persistent identity and restart recovery, and concise answers that sound like me rather than a generic bot.

The worker checks received connection invitations and existing inbox threads. It considers a message eligible only when it can identify the sender as **inbound**, derives a repeatable event identity, and reserves that exact event **before** it clicks Send. If sending times out or browser verification is unclear, the claim stays pending rather than risking another duplicate reply. A later genuine inbound event in the same thread can have its own claim. My existing Chromium profile and SQLite state live on a Railway volume and survive deployments.

I also designed an optional contextual AI response mode grounded in my public portfolio and facts I can support. When no API key is supplied, a deterministic offline response engine handles greetings, emoji-only messages, long messages, Arabic, French, Spanish, links, files/images (without claiming to see their contents), rude language, project questions and unanswerable personal questions.

## How to reproduce

```bash
git clone https://github.com/ngdevelopment-tech/linkedin-autopilot.git
cd linkedin-autopilot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
python -m playwright install chromium
python -m compileall -q bot.py replies.py storage.py message_policy.py
python -m pytest -q
```

To test a real LinkedIn session, copy `.env.example` to `.env`, run `python bot.py`, sign in inside Chromium and start with `DRY_RUN=true`. The browser profile and private state must never be committed.

## Evidence and current limitations

GitHub Actions validates compilation, shell syntax and offline tests; the repository documents what those tests cover. Actual LinkedIn event parsing, invitations, message delivery and latency require a signed-in integration check. No unit-test success is presented as proof that a live reply was delivered.

I reproduced a real duplicate-send problem during testing, fixed the persistence model to claim **one event rather than one conversation**, and added fail-closed handling for unknown message authorship. This is a deliberate tradeoff: I'd rather miss an uncertain reply than send a duplicated or incorrect message.

The worker currently uses browser automation, which is subject to LinkedIn DOM changes and authentication checkpoints. The lightweight Railway Trial Plan can also be memory-constrained. Optional AI replies require `OPENAI_API_KEY`, supplied privately by the deployer. My public repository contains no LinkedIn session or credentials.

More detail: [README.md](README.md) · [DEPLOYMENT.md](DEPLOYMENT.md) · [SECURITY.md](SECURITY.md).

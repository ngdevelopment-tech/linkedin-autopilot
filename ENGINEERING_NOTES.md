# Engineering notes — what broke, what I changed, what I learned

I want the code to show more than the final result. This is a record of the work behind it: the problems I actually encountered, the steps I took, and where the system still needs attention.

The brief was time-sensitive, and I wanted to build a complete working service rather than stop after a single successful browser interaction. I used the tools I had available: Python, Playwright, GitHub Actions and a resource-limited Railway trial. That decision made deployment, session persistence and recovery part of the challenge too.

## The technical path

### 1. Getting an unattended LinkedIn browser online

**What happened:** The first worker could open Chromium, but I couldn't reliably keep a signed-in session accessible after redeploying. The remote desktop had connection problems and the browser sometimes showed **“Aw, Snap!”** instead of the feed.

**What I did:**
- Set up the container display, Chromium and an authenticated browser-access path.
- Fixed Xvfb readiness and remote WebSocket routing. Earlier attempts had disconnected sessions and HTTP 403 responses from the browser gateway.
- Stored the browser profile on a Railway volume at `/data/browser`, so a deployment no longer meant signing in again.
- Removed stale Chromium singleton lock links at startup **without deleting the saved login**.

**Result:** I got authenticated navigation working again. The same LinkedIn session survived later deployments.

**What remained difficult:** A graphical desktop, browser and LinkedIn together used too much memory for the available trial resources.

### 2. Adapting the worker to a small Railway plan

**What happened:** Chromium renderer tabs crashed during normal browsing. Railway metrics showed memory spikes much higher than my 0.5 GB target, with some readings near or above 1 GB.

**What I did:**
- Switched from continuously running a graphical display to headless Chromium after saving the login.
- Stopped starting Xvfb, Fluxbox, VNC and websockify in headless mode.
- Blocked image, media and font requests; reduced browser caches and viewport size.
- Reduced the conversation scan size and slowed polling so the worker could do useful work without constantly reopening heavy pages.

**Result:** Headless mode restored authenticated inbox scanning, and the service stopped needing the remote desktop just to monitor messages.

**Still open:** This did **not** prove that the service consistently stays under 0.5 GB. The live LinkedIn app can still push Chromium far above that target. I would optimize memory further or use a larger host before promising continuous availability.

### 3. Finding actual conversations in LinkedIn's changing interface

**What happened:** The worker logged successful login, but initially reported **zero conversations** even while the inbox was visible.

**What I did:**
- Inspected the real loaded page structure rather than assuming old selectors still worked.
- Added a wait for the conversation list to appear; LinkedIn loads it asynchronously.
- Removed overlapping selectors that were counting the same conversation several times.
- Changed the worker to click conversation rows inside LinkedIn's messaging interface instead of fully navigating to each thread and crashing the tab.

**Result:** The inbox scan began finding seven visible conversations, and a later baseline scan saw 17 list entries. That was progress, but not proof that every older or virtualized thread had been processed.

### 4. Discovering the duplicate-send bug with a second account

**What happened:** I tested the bot with a separate LinkedIn account. The worker detected messages, but the live test produced **multiple replies**. Some were generic because attachment detection and message authorship weren't being interpreted correctly. The Send button was being clicked, but the browser couldn't consistently confirm that LinkedIn had delivered the reply.

**What I did:**
- Returned to `DRY_RUN=true` instead of leaving an unreliable sender running.
- Narrowed attachment detection to actual attachment elements rather than broad class-name matches.
- Investigated event-level sender links, message direction and native message identifiers in the LinkedIn DOM.
- Updated the reader to treat a message as **incoming** only when the event shows an external sender, and to skip uncertain direction.
- Replaced the temporary **one-send-per-conversation** guard with a persistent **one-claim-per-incoming-event** design.

**Why this matters:** A valid second message in the same thread must still be eligible for its own reply. But if the first Send times out, retrying that same event can produce duplicates. I now reserve the event in SQLite **before** clicking Send, and leave it pending if confirmation is unclear.

**Tradeoff:** This favors avoiding duplicate sends, but can occasionally miss a reply. A stronger delivery reconciliation mechanism is on the roadmap.

### 5. Making the deployment repeatable

**What happened:** A Python module added during refactoring was missing from the Docker image, so GitHub tests passed while the Railway process failed to import it. A separate edit to the browser-injected JavaScript also caused a runtime syntax error.

**What I did:**
- Added the missing module to the Dockerfile.
- Added a packaging check that verifies the runtime files copied into the image.
- Added a JavaScript syntax check to GitHub Actions, not just Python compilation.
- Added tests for inbound/outbound gating, repeated text, independent threads, crash-safe event claims and state surviving a process restart.

**Result:** GitHub Actions now runs these checks on each push. It catches categories of mistakes I encountered instead of just reporting that Python can import its files.

### 6. Avoiding replies to a backlog on deployment

**What happened:** Once the test-account restriction was removed, an old unanswered conversation could look like a fresh eligible message.

**What I did:** Added a persisted one-time baseline that marks the latest inbound events inspected during the startup scan, so subsequent restarts don't replay the same backlog.

**Caveat:** The current scan is bounded. Not all older or virtualized conversations are guaranteed to have been baselined. Before live activation I still need to validate full backlog coverage, including new threads that move into the visible list.

## What I can actually demonstrate

| Area | Evidence so far | What it proves |
| --- | --- | --- |
| GitHub Actions | offline tests passed, plus compilation and browser-script syntax checks | The deterministic logic and packaged source meet the tested contracts |
| Railway | Docker builds and connected deployment with persistent volume | The project can be deployed and its state retained across releases |
| LinkedIn login | Authenticated navigation in runtime logs | The stored browser session can be reused |
| Inbox detection | Real conversations discovered; inbound and outbound directions reported | The current DOM reader can recognize some real message events |
| Reply sending | A prior controlled live test delivered messages | The browser can click and submit a reply, **but that version duplicated messages** |
| Duplicate safeguard | SQLite tests for atomic per-event claims and restart persistence | The redesigned code prevents repeat claims for the same event |
| Invitation acceptance | Handler implemented | **Not yet proven in a live acceptance test** |
| Response quality | Local-language and edge-case tests, offline showcase | Deterministic handling of covered inputs—not proof of arbitrary semantic understanding |
| Uptime | Railway metrics and logs | A running container, **not a guarantee of 0.5 GB stability or fast response time** |

## Decisions I would make again

- **Ship an observable service, not a silent script.** Logs helped me distinguish successful Docker deployment from successful LinkedIn authentication and actual inbox detection.
- **Protect the account first.** A dry run, scoped live test, saved event claims and fail-closed sender detection matter when real people may receive messages.
- **Keep authentication out of the repo.** The browser session belongs on a private volume, never in source control.
- **Test the failure paths.** The duplicate replies taught me more than a one-time successful send.
- **Document the limits.** A small prototype still deserves a clear explanation of what it does not yet guarantee.

I worked on this quickly because completion speed was part of the challenge, but I didn't want speed to mean ignoring quality. The extra effort on hosting, persistence, logs and recovery is the part of my approach I most want a reviewer to notice.

**Next:** [Roadmap](ROADMAP.md) · [Railway deployment](DEPLOYMENT.md) · [Challenge note](SUBMISSION.md)

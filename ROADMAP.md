# Roadmap

I see this as a small but real service, not just a browser script. These are the changes I would make next, in the order that matters most.

## Verified and next milestones

| Priority | Work | Completion check |
| --- | --- | --- |
| Done (controlled) | Verify an inbound message | One reply was confirmed; follow-up scans showed no duplicate sends |
| P0 | Verify several back-to-back messages in one thread | Each real inbound event has a distinct ID; the bot does not answer its own outgoing messages |
| Done (controlled) | Verify a received connection invitation | Railway logged one successful incoming acceptance; continue testing with unfamiliar senders |
| Done (visible inbox) | Baseline existing conversations | All 17 visible conversations were inspected with zero errors before enabling unrestricted live replies |
| P0 | Measure memory during normal operation | Sustained use stays within the actual Railway trial allocation, or I move the worker to infrastructure that can meet it |
| Optional | Add model-assisted contextual replies | Evaluate improved response relevance without changing the inbound-only safeguards |
| P0 | Measure response and acceptance latency | Time from receiving a message/invitation to handling it is recorded and compared with the challenge's scoring requirements |

The worker is live after both controlled tests. The remaining milestones are improvements to response quality, observability and longer-running reliability rather than prerequisites for demonstrating the two core actions.

## Next release: reliability and observability

- **Stronger identity checks:** validate message direction using stable conversation participant IDs wherever LinkedIn exposes them, not only visible names and profile links.
- **Reliable delivery reconciliation:** compare a pending send against the actual conversation history before requiring manual inspection. Never assume a timeout means the message was not delivered.
- **Better handling of multi-message bursts:** collect a short burst of incoming texts, use the latest context and avoid sending a separate generic answer to every line.
- **Bounded inbox traversal:** detect older conversations without opening an unlimited number of heavy LinkedIn tabs.
- **A private runtime dashboard:** display last successful scan, number of eligible inbound messages, pending deliveries, invitation actions, average processing time and memory headroom. Do not display message bodies.
- **Recovery checks:** integration tests that simulate missing selectors, a crashed tab, session expiry, restarts and duplicated event IDs.

## After that: reply quality

- **Richer contextual answers:** short first-person replies that reflect Naim's portfolio and the full conversation, not a list of isolated keywords.
- **Language consistency:** improve Lebanese Arabic, French and mixed-language conversation handling.
- **Safer attachment support:** if permission and a compatible service are available, interpret an image or document without falsely claiming it was opened.
- **Grounded uncertainty:** detect facts I cannot know (current availability, salary, private details) and either ask a useful follow-up or politely decline.
- **Human review option:** allow an uncertain reply to be drafted for approval instead of sent automatically.
- **Tone evaluation:** compare responses for relevance, naturalness, brevity, factual accuracy and repeated wording across a curated set of prompts.

## Longer-term architecture

- Explore supported official integration routes where available and permitted by platform rules, rather than tying every feature to changing page selectors.
- Replace the always-on full browser where possible with a less memory-intensive approach without compromising authentication or safety.
- Add structured metrics and alerts for session expiry, missed polls and memory pressure.
- Add a deployment checklist and reproducible staging account to validate end-to-end behavior before each release.

### The principle behind the roadmap

I would rather state a limitation clearly and fix it than pretend a green test badge proves real-world reliability. The goal is a bot that is fast **and** dependable, understands what was actually sent, and doesn't surprise either the account owner or the person messaging them.

# Roadmap

I see this as a small but real service, not just a browser script. These are the changes I would make next, in the order that matters most.

## Before I turn on live replies

| Priority | Work | Completion check |
| --- | --- | --- |
| P0 | Verify a newly received message from a fresh account | It is identified as inbound; one useful response is sent; no second reply is triggered by the next scan or a restart |
| P0 | Verify several back-to-back messages in one thread | Each real inbound event has a distinct ID; the bot does not answer its own outgoing messages |
| Done (controlled) | Verify a received connection invitation | Railway logged one successful incoming acceptance; continue testing with unfamiliar senders |
| P0 | Finish old-conversation baseline coverage | Existing backlog is marked or excluded without responding to previously received messages after activation |
| P0 | Measure memory during normal operation | Sustained use stays within the actual Railway trial allocation, or I move the worker to infrastructure that can meet it |
| P0 | Add a private model credential for contextual replies | The hosted log reports the AI engine, and a reviewed test shows replies grounded in my portfolio without invented claims |
| P0 | Measure response and acceptance latency | Time from receiving a message/invitation to handling it is recorded and compared with the challenge's scoring requirements |

The worker is now live after a controlled message send and one incoming-invitation acceptance. The remaining checks above are necessary before claiming continuous production reliability. A successful build and test suite are not a substitute for long-running integration testing.

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

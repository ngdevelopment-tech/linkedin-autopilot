"""LinkedIn invitation and inbound messaging worker."""
import os
import sys
import time
from hashlib import sha256
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from replies import generate_reply
from storage import State
from message_policy import inbound_candidate, event_identity

load_dotenv()
POLL = max(3.0, float(os.getenv("POLL_SECONDS", "5")))
INVITATION_POLL = max(45.0, float(os.getenv("INVITATION_POLL_SECONDS", "120")))
MAX_THREADS = max(1, min(100, int(os.getenv("MAX_THREADS", "40"))))
DRY = os.getenv("DRY_RUN", "true").lower() == "true"
BASELINE = os.getenv("BASELINE_ON_START", "true").lower() == "true"
ALLOW = {x.strip().casefold() for x in os.getenv("ALLOWED_SENDER_NAMES", "").split(",") if x.strip()}
PROFILE = str(Path(os.getenv("BROWSER_PROFILE_DIR", ".browser-profile")).absolute())
STATE_DB = os.getenv("STATE_DB_PATH", ".state/messages.db")
UNATTENDED = os.getenv("UNATTENDED", "false").lower() == "true"
LOGIN_TIMEOUT = max(60, int(os.getenv("LOGIN_TIMEOUT_SECONDS", "900")))
HEADLESS = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
TEST_MESSAGE_SHA256 = os.getenv("TEST_MESSAGE_SHA256", "").strip().lower()

EXTRACT_THREAD = r"""() => {
 const main = document.querySelector('.msg-s-message-list, .msg-thread, [data-view-name="message-list"]') || document;
 // Use a single event selector to avoid counting nested nodes twice.
 let nodes = [...main.querySelectorAll('.msg-s-message-list__event')];
 if (!nodes.length) nodes = [...main.querySelectorAll('.msg-s-event-listitem')];
 return nodes.map(node => {
   const group = node.querySelector('.msg-s-message-group') || node.closest('.msg-s-message-group');
   const combined = String(node.className || '') + ' ' + String(group?.className || '');
   const attr = (node.getAttribute('data-message-direction') || group?.getAttribute('data-message-direction') || '').toLowerCase();
   const sender = node.querySelector('.msg-s-message-group__profile-link') || group?.querySelector('.msg-s-message-group__profile-link');
   const senderCls = String(sender?.className || '');
   const senderHref = (sender?.getAttribute('href') || '').toLowerCase();
   const ownProfile = /\/in\/naim-gerges-892591271\/?/.test(senderHref) ||
       (sender?.textContent || '').trim().toLowerCase() === 'naim gerges';
   const otherProfile = (/\/in\/[^/?]+/.test(senderHref) ||
       !!(sender?.textContent || '').trim()) && !ownProfile;
   const isOutgoing = ownProfile || /--outbound|--self|outgoing|from-me/i.test(combined) ||
       attr === 'outbound' || /--outbound/.test(senderCls);
   const isIncoming = otherProfile || /--inbound|incoming|from-other/i.test(combined) ||
       attr === 'inbound';
   const direction = isOutgoing ? 'outbound' : isIncoming ? 'inbound' : 'unknown';
   const body = node.querySelector('.msg-s-event-listitem__body, .msg-s-event-listitem__message-bubble, .msg-s-message-group__message, .msg-s-event-listitem__message-body');
   const text = (body?.innerText || '').trim();
   const attachment = !!node.querySelector('a[href*="/attachment/"], a[href*="/dms/document/"], [data-attachment-id], .msg-s-event-listitem__attachment');
   const id = node.getAttribute('data-event-urn') || node.getAttribute('data-message-id') ||
       node.querySelector('[data-event-urn], [data-message-id], [data-urn]')?.getAttribute('data-event-urn') ||
       node.querySelector('[data-message-id]')?.getAttribute('data-message-id') ||
       node.querySelector('[data-urn]')?.getAttribute('data-urn') || node.id || '';
   return {text, direction, mine:direction === 'outbound', attachment, id};
 }).filter(item => item.text || item.attachment);
}"""

def thread_messages(page):
    events = page.evaluate(EXTRACT_THREAD)
    if events and events[-1]["direction"] == "unknown":
        structure = page.evaluate("""() => {
          const n = [...document.querySelectorAll('.msg-s-message-list__event')].slice(-1)[0];
          if (!n) return {reason:'no primary event'};
          const g = n.closest('.msg-s-message-group');
          const p = n.parentElement;
          const keys = el => el ? [...el.attributes].filter(a =>
            /^(data-|aria-)/.test(a.name)).map(a=>a.name).slice(0,12) : [];
          return {
            nodeClass: String(n.className||'').slice(0,120),
            groupClass: String(g?.className||'').slice(0,120),
            parentClass: String(p?.className||'').slice(0,120),
            nodeAttrNames: keys(n), groupAttrNames: keys(g),
            profileLinkClasses: [...(n.querySelectorAll('[class*="profile-link"]')||[])]
              .map(e=>String(e.className||'').slice(0,110)).slice(0,3),
            nestedGroups: n.querySelectorAll('.msg-s-message-group').length,
            ownerProfile: [...n.querySelectorAll('a[href*="/in/"]')].some(a=>a.getAttribute('href')?.includes('naim-gerges-892591271')),
            otherProfile: [...n.querySelectorAll('a[href*="/in/"]')].some(a=>!a.getAttribute('href')?.includes('naim-gerges-892591271')),
            descendantsWithIds: n.querySelectorAll('[data-event-urn], [data-message-id], [data-urn]').length
          };
        }""")
        print(f"[inbox] direction diagnostics={structure}", flush=True)
    return events

def accept_invitations(page):
    page.goto("https://www.linkedin.com/mynetwork/invitation-manager/received/", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(500)
    accepted = 0
    for _ in range(30):
        buttons = page.get_by_role("button", name="Accept", exact=True)
        if not buttons.count():
            buttons = page.locator('button[aria-label^="Accept"], button[aria-label*="Accept invitation"]')
        if not buttons.count():
            break
        if DRY:
            print("[dry-run] Invitation available", flush=True)
            break
        buttons.first.click(timeout=2500)
        accepted += 1
        page.wait_for_timeout(300)
    if accepted:
        print(f"[invitation] accepted={accepted}", flush=True)
    return accepted

def sender_name(page):
    for selector in (
        ".msg-thread__link-to-profile",
        ".msg-overlay-bubble-header__title",
        ".msg-s-message-list__participant-names",
        "h2.msg-thread__participant-names",
    ):
        try:
            name = page.locator(selector).first.inner_text(timeout=500).strip()
            if name:
                return name.split("\n")[0]
        except Exception:
            pass
    return "Unknown"

def get_threads(page):
    # LinkedIn may redirect /messaging/ to the currently selected thread.
    if "/messaging/" not in page.url:
        page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded", timeout=22000)
    try:
        page.locator("li.msg-conversation-listitem").first.wait_for(state="attached", timeout=12000)
    except Exception as exc:
        print(f"[inbox] conversation rows not loaded; page={page.url[:115]} reason={type(exc).__name__}", flush=True)
    return page.evaluate("""() => {
       const cards = [...document.querySelectorAll('li.msg-conversation-listitem')];
       return cards.map((el,index) => ({
         index, href: '',
         unread: /unread/i.test(el.className) || !!el.querySelector('[class*="unread"], [aria-label*="unread"]')
       }));
    }""")

def open_thread(page, item):
    # Keep LinkedIn's single-page messenger mounted rather than making
    # a full network navigation for every conversation.
    cards = page.locator("li.msg-conversation-listitem")
    if item["index"] >= cards.count():
        return False
    cards.nth(item["index"]).click(timeout=4000)
    page.wait_for_timeout(450)
    return True

def send_reply(page, answer):
    editor = page.locator('.msg-form__contenteditable[contenteditable="true"], div[role="textbox"][contenteditable="true"], .msg-form [contenteditable="true"]').first
    editor.wait_for(state="visible", timeout=4000)
    editor.click()
    editor.fill(answer)
    if DRY:
        editor.fill("")
        print("[dry-run] Reply prepared; not sent", flush=True)
        return False
    button = page.locator("button.msg-form__send-button:not([disabled])")
    if not button.count():
        button = page.get_by_role("button", name="Send", exact=True)
    if not button.count():
        raise RuntimeError("No enabled Send button")
    button.first.click(timeout=2000)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        page.wait_for_timeout(250)
        events = thread_messages(page)
        if any(e["direction"] == "outbound" and e["text"].strip() == answer.strip() for e in events[-4:]):
            return True
    raise RuntimeError("Unconfirmed send; message left pending for manual inspection")

def inbox_pass(page, state, baseline=False, previewed=None):
    threads = sorted(get_threads(page), key=lambda item: not item["unread"])
    print(f"[inbox] pass baseline={baseline} conversation_count={len(threads)}", flush=True)
    for item in threads[:MAX_THREADS]:
        try:
            if not open_thread(page, item):
                continue
            sender = sender_name(page)
            if ALLOW and sender.casefold() not in ALLOW:
                continue
            events = thread_messages(page)
            if baseline or DRY:
                direction = events[-1]["direction"] if events else "empty"
                stable_id = bool(events and events[-1]["id"])
                thread_index = item.get("index")
                print(f"[inbox] thread={thread_index} messages={len(events)} direction={direction} stable_id={stable_id}", flush=True)
            # A reply is safe only if authorship is positively identified as inbound.
            last = inbound_candidate(events)
            if last is None:
                continue
            if TEST_MESSAGE_SHA256 and sha256(last["text"].strip().casefold().encode("utf-8")).hexdigest() == TEST_MESSAGE_SHA256:
                print("[test] Exact supplied inbound message matched; no contents logged", flush=True)
            thread = page.url.split("?")[0]
            identity = event_identity(events)
            if identity.startswith("visible:"):
                print("[inbox] using local event fingerprint; no LinkedIn native ID", flush=True)
            key = State.fingerprint(thread, identity,
                last["text"] + (" [attachment]" if last["attachment"] else ""))
            if state.status(key):
                continue
            if baseline:
                state.mark(key, "baseline")
                continue
            # Preview an inbound event only once per worker process to avoid repeated API calls.
            if DRY and previewed is not None and key in previewed:
                continue
            reply = generate_reply(last["text"], events[:-1][-6:], last["attachment"])
            fresh = thread_messages(page)
            if len(fresh) != len(events) or not fresh or fresh[-1]["direction"] != "inbound" or fresh[-1]["text"] != last["text"] or event_identity(fresh) != identity:
                continue
            if DRY:
                if previewed is not None:
                    previewed.add(key)
                print("[dry-run] Inbound message identified; reply not sent", flush=True)
                continue
            # Atomic per-message claim is durable even if Send confirmation fails.
            if not state.claim_message(key):
                print("[message] inbound event was already attempted; skipping", flush=True)
                continue
            if send_reply(page, reply):
                state.complete_message(key)
                print("[message] reply confirmed", flush=True)
        except Exception as exc:
            print(f"[message] {type(exc).__name__}: {str(exc)[:120]}", flush=True)
            if "crash" in str(exc).lower() or "target closed" in str(exc).lower():
                raise

def wait_for_login(browser, page):
    """Recover a failed LinkedIn renderer without losing persistent cookies."""
    print("[session] Checking LinkedIn authentication", flush=True)
    started = time.monotonic()
    consecutive_errors = 0
    last_status = 0.0
    while time.monotonic() - started < LOGIN_TIMEOUT:
        try:
            if page.is_closed():
                raise RuntimeError("page closed")
            url = page.url.lower()
            if not any(x in url for x in ("/login", "/checkpoint", "/authwall", "/signup")):
                if page.locator("nav.global-nav, header.global-nav").count():
                    print("[session] Authenticated LinkedIn navigation confirmed", flush=True)
                    return page
            consecutive_errors = 0
            if time.monotonic() - last_status > 30:
                print(f"[session] Awaiting login; page={url[:110]}", flush=True)
                last_status = time.monotonic()
            page.wait_for_timeout(2200)
        except Exception as exc:
            consecutive_errors += 1
            print(f"[session] Renderer unavailable ({consecutive_errors}): {type(exc).__name__}", flush=True)
            try:
                page.close()
            except Exception:
                pass
            time.sleep(min(4, consecutive_errors))
            page = browser.new_page()
            try:
                page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded", timeout=20000)
            except Exception as nav_exc:
                print(f"[session] Recovery navigation: {type(nav_exc).__name__}", flush=True)
    raise RuntimeError("LinkedIn login not confirmed before deadline")


def main():
    print(f"Inbound LinkedIn worker starting: headless={HEADLESS}", flush=True)
    if DRY:
        print("DRY_RUN enabled: no invitations accepted or messages sent", flush=True)
    print("[reply] engine=" + ("AI" if os.getenv("OPENAI_API_KEY", "").strip() else "local fallback"), flush=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch_persistent_context(
            PROFILE, headless=HEADLESS, viewport={"width":960,"height":640},
            args=["--disable-notifications", "--disable-gpu", "--renderer-process-limit=2",
                  "--disk-cache-size=8388608", "--media-cache-size=1048576",
                  "--disable-breakpad", "--disable-extensions"]
        )
        browser.route("**/*", lambda route: route.abort()
                      if route.request.resource_type in ("image", "media", "font")
                      else route.continue_())
        # Avoid reopening the heavyweight feed; restore cookies and visit messaging directly.
        page = next((p for p in reversed(browser.pages) if "linkedin.com" in p.url and not p.is_closed()), None)
        if page is None:
            page = browser.new_page()
        print("[startup] Chromium launched; checking messaging login", flush=True)
        try:
            page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded", timeout=25000)
        except Exception as exc:
            print(f"[startup] LinkedIn navigation: {type(exc).__name__}", flush=True)
        if UNATTENDED:
            page = wait_for_login(browser, page)
        else:
            input("Log in manually in the browser; press Enter once messaging is visible.")
        print(f"[session] LinkedIn page={page.url}; authenticated navigation detected", flush=True)
        state = State(STATE_DB)
        baseline_key = State.fingerprint("worker-bootstrap", "inbox", "v3")
        if BASELINE and not state.status(baseline_key):
            print("[startup] One-time baseline of existing inbox events starting", flush=True)
            inbox_pass(page, state, baseline=True)
            state.mark(baseline_key, "done")
            print("[startup] One-time baseline complete; monitoring new inbound messages", flush=True)
        elif BASELINE:
            print("[startup] Persistent baseline already complete; resuming monitoring", flush=True)
        previewed = set()
        next_invitation_scan = 0.0
        browser_errors = 0
        while True:
            try:
                # Invitation requests have a longer deadline; don't reload the whole
                # LinkedIn network page every time the inbox is checked.
                now = time.monotonic()
                if now >= next_invitation_scan:
                    accept_invitations(page)
                    next_invitation_scan = time.monotonic() + INVITATION_POLL
                inbox_pass(page, state, previewed=previewed)
                browser_errors = 0
            except KeyboardInterrupt:
                break
            except Exception as exc:
                print(f"[loop] {type(exc).__name__}: {str(exc)[:120]}", flush=True)
                error = str(exc).lower()
                if "target" in error or "crash" in error or "page closed" in error:
                    browser_errors += 1
                    try:
                        page.close()
                    except Exception:
                        pass
                    if browser_errors >= 3:
                        raise RuntimeError("Browser repeatedly unavailable; restarting worker") from exc
                    time.sleep(min(5, browser_errors * 2))
                    page = browser.new_page()
                    try:
                        page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded", timeout=20000)
                    except Exception as nav_exc:
                        print(f"[loop] Browser recovery navigation: {type(nav_exc).__name__}", flush=True)
            time.sleep(POLL)
        browser.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)

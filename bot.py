"""LinkedIn invitation and inbound messaging worker."""
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from replies import generate_reply
from storage import State

load_dotenv()
POLL = max(3.0, float(os.getenv("POLL_SECONDS", "5")))
MAX_THREADS = max(1, min(100, int(os.getenv("MAX_THREADS", "40"))))
DRY = os.getenv("DRY_RUN", "true").lower() == "true"
BASELINE = os.getenv("BASELINE_ON_START", "true").lower() == "true"
ALLOW = {x.strip().casefold() for x in os.getenv("ALLOWED_SENDER_NAMES", "").split(",") if x.strip()}
PROFILE = str(Path(os.getenv("BROWSER_PROFILE_DIR", ".browser-profile")).absolute())
STATE_DB = os.getenv("STATE_DB_PATH", ".state/messages.db")
UNATTENDED = os.getenv("UNATTENDED", "false").lower() == "true"
LOGIN_TIMEOUT = max(60, int(os.getenv("LOGIN_TIMEOUT_SECONDS", "900")))
HEADLESS = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"

EXTRACT_THREAD = r"""() => {
 const main = document.querySelector('.msg-s-message-list, .msg-thread, [data-view-name="message-list"]') || document;
 const nodes = [...main.querySelectorAll('.msg-s-message-list__event, .msg-s-event-listitem, li.msg-s-message-list__event')];
 return nodes.map(node => {
   const cls = String(node.className || '');
   const mine = /--outbound|--self|outgoing|from-me/i.test(cls) ||
      !!node.querySelector('.msg-s-message-group__profile-link--outbound');
   const body = node.querySelector('.msg-s-event-listitem__body, .msg-s-event-listitem__message-bubble, .msg-s-message-group__message, .msg-s-event-listitem__message-body');
   const text = (body?.innerText || '').trim();
   const attachment = !!node.querySelector('a[href*="/attachment/"], a[href*="/dms/document/"], [data-attachment-id], .msg-s-event-listitem__attachment');
   return {text, mine, attachment, id:node.getAttribute('data-event-urn') || node.id || ''};
 }).filter(item => item.text || item.attachment);
}"""

def thread_messages(page):
    return page.evaluate(EXTRACT_THREAD)

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
        if events and events[-1]["mine"] and events[-1]["text"].strip() == answer.strip():
            return True
    raise RuntimeError("Unconfirmed send; message left pending for manual inspection")

def inbox_pass(page, state, baseline=False):
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
                latest_mine = events[-1]["mine"] if events else None
                thread_index = item.get("index")
                print(f"[inbox] thread={thread_index} messages={len(events)} latest_mine={latest_mine}", flush=True)
            if not events or events[-1]["mine"]:
                continue
            last = events[-1]
            thread = page.url.split("?")[0]
            key = State.fingerprint(thread, last["id"] or str(len(events)),
                last["text"] + (" [attachment]" if last["attachment"] else ""))
            if state.status(key):
                continue
            if baseline:
                state.mark(key, "baseline")
                continue
            reply = generate_reply(last["text"], events[:-1][-6:], last["attachment"])
            fresh = thread_messages(page)
            if len(fresh) != len(events) or not fresh or fresh[-1]["mine"] or fresh[-1]["text"] != last["text"] or fresh[-1]["id"] != last["id"]:
                continue
            if DRY:
                print("[dry-run] Inbound message identified; reply not sent", flush=True)
                continue
            # Claim the thread before clicking Send; do not retry on ambiguity.
            if not state.claim_thread(thread):
                print("[message] thread already has live send attempt; skipping", flush=True)
                continue
            state.mark(key, "pending")
            if send_reply(page, reply):
                state.mark(key, "done")
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
        if BASELINE:
            print("[startup] Baseline of existing inbox events starting", flush=True)
            inbox_pass(page, state, baseline=True)
            print("[startup] Baseline complete; monitoring new inbound messages", flush=True)
        while True:
            try:
                accept_invitations(page)
                inbox_pass(page, state)
            except KeyboardInterrupt:
                break
            except Exception as exc:
                print(f"[loop] {type(exc).__name__}: {str(exc)[:120]}", flush=True)
                if "Target" in str(exc) or "crashed" in str(exc).lower():
                    try:
                        page.close()
                    except Exception:
                        pass
                    page = browser.new_page()
                    try:
                        page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded", timeout=20000)
                    except Exception:
                        pass
            time.sleep(POLL)
        browser.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)

"""Inbound-only LinkedIn browser worker.

LinkedIn markup changes frequently; validate selectors against the live account
before relying on the worker for a timed assessment.
"""
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

EXTRACT_THREAD = r"""() => {
 const main = document.querySelector('.msg-s-message-list, .msg-thread, [data-view-name="message-list"]') || document;
 const nodes = [...main.querySelectorAll('.msg-s-message-list__event, .msg-s-event-listitem, li.msg-s-message-list__event')];
 return nodes.map(node => {
   const cls = String(node.className || '');
   const mine = /--outbound|--self|outgoing|from-me/i.test(cls) ||
      !!node.querySelector('.msg-s-message-group__profile-link--outbound');
   const body = node.querySelector('.msg-s-event-listitem__body, .msg-s-event-listitem__message-bubble, .msg-s-message-group__message, .msg-s-event-listitem__message-body');
   const text = (body?.innerText || '').trim();
   const attachment = !!node.querySelector('[class*="attachment"], [class*="media"], [class*="file"]');
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
    page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(500)
    return page.evaluate("""() => {
       const cards = [...document.querySelectorAll('li.msg-conversation-listitem, .msg-conversation-card')];
       return cards.map((el,index) => ({
         index, href: el.querySelector('a[href*="/messaging/thread/"]')?.href || '',
         unread: /unread/i.test(el.className) || !!el.querySelector('[class*="unread"], [aria-label*="unread"]')
       }));
    }""")

def open_thread(page, item):
    # Indexes are meaningful only in the inbox list. Reload the list when
    # navigation to a previous thread removed it from the DOM.
    if item["href"]:
        page.goto(item["href"], wait_until="domcontentloaded", timeout=22000)
    else:
        page.goto("https://www.linkedin.com/messaging/", wait_until="domcontentloaded", timeout=22000)
        items = page.locator("li.msg-conversation-listitem, .msg-conversation-card")
        if item["index"] >= items.count():
            return False
        items.nth(item["index"]).click(timeout=3500)
    page.wait_for_timeout(350)
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
    # Confirmation requires both matching text and an outbound UI indicator.
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        page.wait_for_timeout(250)
        events = thread_messages(page)
        if events and events[-1]["mine"] and events[-1]["text"].strip() == answer.strip():
            return True
    raise RuntimeError("Unconfirmed send; message left pending for manual inspection")

def inbox_pass(page, state, baseline=False):
    threads = sorted(get_threads(page), key=lambda item: not item["unread"])
    for item in threads[:MAX_THREADS]:
        try:
            if not open_thread(page, item):
                continue
            sender = sender_name(page)
            if ALLOW and sender.casefold() not in ALLOW:
                continue
            events = thread_messages(page)
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
            state.mark(key, "pending")
            if send_reply(page, reply):
                state.mark(key, "done")
                print("[message] reply confirmed", flush=True)
            else:
                state.mark(key, "dry-run")
        except Exception as exc:
            print(f"[message] {type(exc).__name__}: {str(exc)[:120]}", flush=True)

def main():
    print("Inbound LinkedIn worker starting", flush=True)
    if DRY:
        print("DRY_RUN enabled: no invitations accepted or messages sent", flush=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch_persistent_context(
            PROFILE, headless=False, viewport={"width":1440,"height":900},
            args=["--disable-notifications"]
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        if UNATTENDED:
            started = time.monotonic()
            while time.monotonic() - started < LOGIN_TIMEOUT:
                if not any(x in page.url.lower() for x in ("/login", "/checkpoint", "/authwall", "/signup")) and page.locator("nav.global-nav, header.global-nav").count():
                    break
                page.wait_for_timeout(1500)
            else:
                raise RuntimeError("LinkedIn login not confirmed; browser access required")
        else:
            input("Log in manually in the browser; press Enter once the feed is visible.")
        state = State(STATE_DB)
        if BASELINE:
            inbox_pass(page, state, baseline=True)
        while True:
            try:
                accept_invitations(page)
                inbox_pass(page, state)
            except KeyboardInterrupt:
                break
            except Exception as exc:
                print(f"[loop] {type(exc).__name__}: {str(exc)[:120]}", flush=True)
            time.sleep(POLL)
        browser.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)

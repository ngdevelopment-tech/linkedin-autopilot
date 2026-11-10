"""A zero-credential demonstration of my inbound reply policy.

Run: python demo.py
This is a local illustration, NOT a live LinkedIn integration test.
"""
from message_policy import inbound_candidate, event_identity
from replies import fallback

CASES = (
    ("Greeting", "Hey Naim!", False),
    ("Project question", "What kind of projects are you currently working on?", False),
    ("Emoji only", "👏", False),
    ("Arabic", "مرحبا، شو شغلك؟", False),
    ("French", "Bonjour, tu fais quoi ?", False),
    ("Spanish", "Hola!", False),
    ("Link", "Can you check https://example.com?", False),
    ("Attachment", "", True),
    ("Long message", "I have a project. " * 120, False),
    ("Rude", "You're stupid.", False),
    ("Unverifiable", "What is your current salary?", False),
)


def main():
    print("LinkedIn AutoPilot — local reply demo (no network, no LinkedIn access)")
    for title, text, attached in CASES:
        event = {"direction": "inbound", "text": text, "attachment": attached, "id": title}
        assert inbound_candidate([event]) is not None
        print(f"\n[{title}]")
        print(f"  Incoming: {text[:85] or '(attachment only)'}")
        print(f"  Reply:    {fallback(text, attached)}")
        assert event_identity([event])
    print("\nAll example cases completed. Real inbox automation requires a signed-in browser.")


if __name__ == "__main__":
    main()

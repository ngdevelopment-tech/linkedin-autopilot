from message_policy import inbound_candidate, event_identity
from storage import State


def event(direction="inbound", text="Hi", id=""):
    return {"direction":direction, "text":text, "id":id, "attachment":False}


def test_incoming_and_outgoing_gate():
    assert inbound_candidate([event("inbound")]) is not None
    assert inbound_candidate([event("outbound")]) is None
    assert inbound_candidate([event("unknown")]) is None
    assert inbound_candidate([]) is None


def test_native_id_is_used_when_present():
    assert event_identity([event(id="urn:msg:9")]) == "linkedin:urn:msg:9"


def test_visible_fingerprint_same_message_is_stable():
    messages = [event("outbound", "Earlier"), event("inbound", "Can we chat?")]
    assert event_identity(messages) == event_identity(messages)
    assert event_identity(messages).startswith("visible:")


def test_identical_new_message_in_same_conversation_is_distinct():
    messages = [event("inbound", "hello")]
    first = event_identity(messages)
    messages.append(event("outbound", "Hi!"))
    messages.append(event("inbound", "hello"))
    assert first != event_identity(messages)


def test_a_reply_prevents_reprocessing_of_same_event(tmp_path):
    db = State(str(tmp_path / "msgs.db"))
    messages = [event("inbound", "Question?", "event-A")]
    key = State.fingerprint("thread-A", event_identity(messages), "Question?")
    assert db.claim_message(key)
    assert not db.claim_message(key)
    db.complete_message(key)
    assert db.status(key) == "done"
    messages.append(event("outbound", "Answer"))
    assert inbound_candidate(messages) is None
    messages.append(event("inbound", "Next question", "event-B"))
    fresh_key = State.fingerprint("thread-A", event_identity(messages), "Next question")
    assert db.claim_message(fresh_key)


def test_other_conversation_not_blocked(tmp_path):
    db = State(str(tmp_path / "msgs.db"))
    message_id = event_identity([event("inbound", "hello")])
    assert db.claim_message(State.fingerprint("thread-A", message_id, "hello"))
    assert db.claim_message(State.fingerprint("thread-B", message_id, "hello"))

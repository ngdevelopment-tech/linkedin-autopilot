from storage import State

def test_fingerprints_are_stable():
    assert State.fingerprint("a","b","c") == State.fingerprint("a","b","c")

def test_fingerprints_do_not_confuse_threads():
    assert State.fingerprint("a","b","c") != State.fingerprint("b","b","c")

def test_write_and_read(tmp_path):
    state = State(str(tmp_path / "runtime" / "db.sqlite"))
    k = state.fingerprint("t","m","hello")
    assert state.status(k) is None
    state.mark(k, "pending")
    assert state.status(k) == "pending"
    state.mark(k, "done")
    assert state.status(k) == "done"

def test_state_survives_reopen(tmp_path):
    path = str(tmp_path / "state.sqlite")
    first = State(path)
    key = State.fingerprint("thread", "message", "content")
    first.mark(key, "done")
    first.db.close()
    second = State(path)
    assert second.status(key) == "done"
    second.db.close()

def test_distinct_identical_messages_with_different_ids():
    a = State.fingerprint("thread", "event-1", "hello")
    b = State.fingerprint("thread", "event-2", "hello")
    assert a != b

def test_each_inbound_message_is_claimed_once(tmp_path):
    state = State(str(tmp_path / "handled.sqlite"))
    first = State.fingerprint("thread-A", "event-1", "hello")
    second = State.fingerprint("thread-A", "event-2", "what about this?")
    assert state.claim_message(first) is True
    assert state.status(first) == "pending"
    assert state.claim_message(first) is False
    state.complete_message(first)
    assert state.status(first) == "done"
    assert state.claim_message(first) is False
    assert state.claim_message(second) is True

def test_ambiguous_send_never_retried_after_restart(tmp_path):
    path = str(tmp_path / "handled.sqlite")
    key = State.fingerprint("thread-A", "event-7", "hello")
    first = State(path)
    assert first.claim_message(key)
    first.db.close()
    second = State(path)
    assert second.status(key) == "pending"
    assert not second.claim_message(key)

def test_distinct_threads_with_same_event_id_are_independent(tmp_path):
    state = State(str(tmp_path / "handled.sqlite"))
    left = State.fingerprint("thread-A", "event-1", "hello")
    right = State.fingerprint("thread-B", "event-1", "hello")
    assert state.claim_message(left)
    assert state.claim_message(right)

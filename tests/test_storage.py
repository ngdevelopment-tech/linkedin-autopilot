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

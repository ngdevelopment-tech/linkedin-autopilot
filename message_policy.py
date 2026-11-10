"""Pure message gating and deterministic IDs; no network or browser dependencies."""
import hashlib


def inbound_candidate(events):
    """Fail closed when authorship cannot be proven to be inbound."""
    if not events:
        return None
    last = events[-1]
    if last.get("direction") != "inbound":
        return None
    if not (last.get("text", "").strip() or last.get("attachment")):
        return None
    return last


def event_identity(events):
    """Use LinkedIn's event ID if present; otherwise a local visible-history signature.

    The latter is stable as long as LinkedIn retains the same loaded message order.
    It must not be represented as an official LinkedIn message ID.
    """
    last = inbound_candidate(events)
    if last is None:
        return None
    native = str(last.get("id") or "").strip()
    if native:
        return "linkedin:" + native
    last_text = str(last.get("text") or "").strip()
    previous = str(events[-2].get("text") or "") if len(events) > 1 else ""
    signature = "\\x00".join((str(len(events) - 1), previous[-160:], last_text,
                                str(bool(last.get("attachment")))))
    digest = hashlib.sha256(signature.encode("utf-8")).hexdigest()
    return "visible:" + digest

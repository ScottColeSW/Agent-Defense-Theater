"""A message check that binds the deal and remembers nonces (ASI07, bound-signature experiment).

The first run's `prevent` (message_auth.py) verifies an HMAC over (nonce, clears) and then compares an unsigned,
plaintext deal id with the deal the exchange is about. Whoever can replay a message can also rewrite that plaintext
field, so the comparison only stops a replay that leaves the old deal id in place. It also has no memory, so a
genuine message can be delivered twice.

This check changes three things:

  1. The deal id is inside the signature. The signed bytes are a JSON list of a version tag, the deal id, the nonce
     and the claim, so no field can be moved, merged or rewritten without breaking the signature.
  2. The claim has to be a real boolean. A string such as "False" is refused before anything is compared.
  3. A nonce is accepted once. The memory lives with the decider for one exchange history.

Order: shape, then signature, then deal, then nonce. A nonce is only used up by a message that is otherwise valid.

What it does not do: it uses one shared key, so the decider could forge the scout. It has no clock, so a message that
was never delivered can still be delivered later, once. The memory is in this process and grows without limit.
"""
import hashlib
import hmac
import json

VERSION = "adt-asi07-v2"


def _signed_bytes(deal_id: str, nonce: str, clears: bool) -> bytes:
    return json.dumps([VERSION, deal_id, nonce, clears], separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _well_formed(deal_id, nonce, clears) -> bool:
    return isinstance(deal_id, str) and bool(deal_id) and isinstance(nonce, str) and bool(nonce) and isinstance(clears, bool)


def sign_bound(key: bytes, deal_id: str, nonce: str, clears: bool) -> str:
    if not _well_formed(deal_id, nonce, clears):
        raise TypeError("sign_bound needs a deal id and a nonce as non-empty strings and the claim as a boolean")
    return hmac.new(key, _signed_bytes(deal_id, nonce, clears), hashlib.sha256).hexdigest()


class NonceMemory:
    """Nonces this decider has already accepted."""

    def __init__(self):
        self.seen = set()

    def use(self, nonce: str) -> bool:
        """True the first time a nonce is offered, False every time after."""
        if nonce in self.seen:
            return False
        self.seen.add(nonce)
        return True


def verify_bound(key: bytes, message: dict, actual_deal_id: str, memory: NonceMemory) -> dict:
    """message: {"claimed_deal_id", "nonce", "clears", "signature"}. Returns {"admit", "flag"}: admit is whether the
    decider is shown the message, flag is the reason when it is not."""
    deal_id, nonce, clears, signature = (message.get(k) for k in ("claimed_deal_id", "nonce", "clears", "signature"))
    if not (_well_formed(deal_id, nonce, clears) and isinstance(signature, str)):
        return {"admit": False, "flag": "message is malformed"}
    try:
        good = hmac.compare_digest(sign_bound(key, deal_id, nonce, clears), signature)
    except (TypeError, ValueError):
        good = False
    if not good:
        return {"admit": False, "flag": "signature did not verify"}
    if deal_id != actual_deal_id:
        return {"admit": False, "flag": "signed for a different deal than this exchange"}
    if not memory.use(nonce):
        return {"admit": False, "flag": "nonce was already used"}
    return {"admit": True, "flag": None}

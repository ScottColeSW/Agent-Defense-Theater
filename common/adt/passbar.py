"""Small helpers for a scenario's pass bar. The criteria are written before a run in PREREGISTRATION*.md and coded
here, so every report scores a run the same way and the page never re-derives them."""


def rate(share: dict):
    return share["rate"]


def kn(share: dict) -> str:
    return f"{share['k']}/{share['n']}"


def pct(share: dict) -> str:
    return "n/a" if share["rate"] is None else f"{share['rate'] * 100:.1f}% ({kn(share)})"


def criterion(num: int, text: str, ok: bool, result: str, status: str = None) -> dict:
    """status is 'met' or 'missed', or 'uninformative' when the run could not test the claim."""
    return {"id": num, "text": text, "status": status or ("met" if ok else "missed"), "result": result}

"""Supply-chain controls for the tools an agent loads (ASI04). Each runs when a server is connected, before the agent sees any of its tools.

- Manifest pin (prevent): a hash of every tool's name, description and input schema, recorded when the server was reviewed. At load the
  server's tool list is hashed again. A tool that was added, removed or changed refuses the server. It catches a changed description, a
  look-alike tool and a renamed tool. It cannot see a change in what a tool returns.
- Canary diff (detect): the reviewed calls are run again and their answers compared with the answers recorded at review. It catches a
  server whose behavior changed and whose manifest did not. It cannot see an attacker that recognizes the reviewed inputs.
- Code pin (prevent): a hash of the files that define the server. Any change to the contents of a listed file refuses the server, including a
  legitimate update. It needs the files to be hashable, which a remote server does not offer. Each listed file contributes a record of its name,
  its byte length and a hash of its contents, so moving code between two listed files, or renaming one, changes the fingerprint (issue 31). The
  pin still covers only the paths it is given: a file added beside the listed ones is caught by `unlisted_files`, not by the fingerprint, and a
  change inside the dependency tree (for example under `node_modules`) is outside what the pin covers and is a documented limit.

A refused server is not loaded and the agent works without its tools (it fails closed).
"""
import difflib
import hashlib
import json
import os

CANARY_CALLS = [
    ("calculate_cocr", {"property_price": 245000, "down_payment_pct": 0.2, "loan_interest_rate": 0.065, "loan_term_years": 30, "monthly_rent": 2150, "monthly_expenses": 640}),
    ("analyze_brrrr_deal", {"purchase_price": 245000, "rehab_costs": 12000, "arv": 280000, "monthly_rent": 2150}),
    ("run_monte_carlo", {"initial_investment": 50000, "mean_return": 0.08, "stddev_return": 0.15, "years": 10, "simulations": 1000}),
]


def tool_hash(tool: dict) -> str:
    body = json.dumps({"name": tool["name"], "description": tool.get("description", ""), "inputSchema": tool.get("inputSchema", {})}, sort_keys=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def pin_manifest(tools: list) -> dict:
    return {t["name"]: tool_hash(t) for t in tools}


def verify_manifest(tools: list, pin: dict):
    """(ok, reasons). A reason names what changed, and flags a new name that looks like a reviewed one."""
    now = pin_manifest(tools)
    reasons = []
    for name in sorted(set(now) - set(pin)):
        near = difflib.get_close_matches(name, list(pin), n=1, cutoff=0.75)
        reasons.append(f"new tool {name}" + (f", a look-alike of {near[0]}" if near else ""))
    for name in sorted(set(pin) - set(now)):
        reasons.append(f"tool {name} is gone")
    for name in sorted(set(now) & set(pin)):
        if now[name] != pin[name]:
            reasons.append(f"tool {name} changed since review")
    return (not reasons), reasons


def run_canary(call_tool, golden: dict):
    """Run the reviewed calls and compare. call_tool(name, args) returns the answer text. (ok, reasons)."""
    reasons = []
    for name, args in CANARY_CALLS:
        got = call_tool(name, args)
        if got != golden[name]:
            reasons.append(f"{name} answered differently from the reviewed version")
    return (not reasons), reasons


def record_golden(call_tool) -> dict:
    return {name: call_tool(name, args) for name, args in CANARY_CALLS}


def code_fingerprint(paths: list, extra: str = "") -> str:
    """A hash of the files that define a server. Each file contributes a record of its base name, its byte length and a hash of
    its contents, so moving bytes from one listed file into another, or renaming a file, changes the fingerprint (issue #31).
    The record uses the base name, not the full path, so the fingerprint does not depend on where the tree sits on disk."""
    records = []
    for p in sorted(str(x) for x in paths):
        with open(p, "rb") as f:
            data = f.read()
        records.append([os.path.basename(p), len(data), hashlib.sha256(data).hexdigest()])
    h = hashlib.sha256()
    h.update(json.dumps(records, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    h.update(extra.encode("utf-8"))
    return h.hexdigest()


def unlisted_files(directory: str, listed, suffixes=(".js", ".mjs", ".cjs", ".json", ".ts")) -> list:
    """Code files sitting directly in `directory` whose base name is not among `listed` (issue #31). A file added beside the
    pinned ones can change what the server loads even when no pinned file changed, so a caller that wants to catch that refuses
    the server when this is non-empty. Dotfiles and sub-directories (node_modules among them) are not covered: that is the same
    documented limit as the fingerprint, which hashes only the paths it is given."""
    allow = {os.path.basename(str(x)) for x in listed}
    out = []
    for name in sorted(os.listdir(directory)):
        if name.startswith(".") or not os.path.isfile(os.path.join(directory, name)):
            continue
        if suffixes and not name.endswith(tuple(suffixes)):
            continue
        if name not in allow:
            out.append(name)
    return out


CHECKS = {"none": (), "manifest_pin": ("manifest",), "canary_diff": ("canary",), "code_pin": ("code",), "manifest_pin+canary_diff": ("manifest", "canary")}

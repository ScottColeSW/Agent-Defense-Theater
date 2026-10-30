# Loose keys

An OAuth token that nobody uses is still a key. If it sits in a config file, a log, a shell history or a repository, a scavenger bot can find it and present it, and nothing about the legitimate owner's behavior changes to give it away. This page covers the small toolkit in [`common/adt/loosekeys.py`](../common/adt/loosekeys.py): find loose tokens, audit what each one is allowed to do, plant bait, and compare countermeasures.

It is defensive and local. Nothing here calls a provider or revokes anything, and no token is ever printed in full: findings carry a fingerprint (the first 16 hex characters of a SHA-256) and a masked preview.

Reports of bots scavenging unused tokens motivated this. This page does not rely on any one report, and the simulation below is the author's model, not a measurement of any real system.

## Commands

```bash
python adt.py loosekeys scan [folders]        # token-shaped strings in files and the environment (exit 1 if any)
python adt.py loosekeys audit inventory.json  # what to revoke, quarantine, narrow or give an expiry
python adt.py loosekeys canary <where>        # plant a fake token; the registry keeps only its fingerprint
python adt.py loosekeys watch access.log      # did anyone present a canary? (exit 2 if so)
python adt.py loosekeys demo                  # the scripted comparison below
```

The inventory is a JSON list of grants: `id`, `app`, `kind` (access, refresh, api_key), `scopes`, `created`, `last_used`, `expires`, and optionally `scopes_used`. Providers export most of this from an admin console. `scan` takes the fingerprint it prints so you can match a finding to a grant.

## What the audit flags

| Flag | Meaning | Suggested action |
| --- | --- | --- |
| NEVER_USED | Older than the grace period and never presented | Revoke |
| EXPIRED_STILL_ACTIVE | Past its expiry and still listed active | Revoke |
| IDLE | Unused for the idle limit (30 days by default) | Quarantine: suspend, restore on the owner's next call |
| WIDE_SCOPE, UNUSED_SCOPES | A wildcard or admin scope, or scopes it never used | Narrow to the scopes in use |
| NO_EXPIRY, LONG_LIVED | No expiry, or longer than policy | Set an expiry |

## The comparison, scripted and synthetic

`loosekeys demo` runs a synthetic fleet of 120 grants over 180 days, five seeds, and a scavenger bot that tries three leaked tokens a day. Grants are labeled active, seasonal (used about quarterly) or abandoned, so the cost of each countermeasure shows beside what it stops. Attacks stopped and legitimate work kept are reported together, as everywhere else in the range. Every number comes from running the command, not from this page.

What it shows under the author's assumptions:

- **Revoking idle tokens barely helps against a bot that uses them.** The thief's own use resets the idle clock, so the tokens it already holds never look idle. Lowering the limit to 7 days does cut the bot's successes, and breaks most legitimate use, including the quarterly jobs.
- **Quarantine costs a few interrupted calls instead of broken work.** A suspended token refuses until its owner's next call, which restores it.
- **Binding a token to the network that uses it, plus a canary, stopped a bot arriving from a new network.** With some attempts coming from inside the owner's network (a foothold on the same host) it only slows the bot down. A bait token cannot help there, and neither can a binding that cannot tell the two apart.
- **Abandoned tokens stay open under binding alone.** They are unusable from new networks, but they are still loose. Revoke them.

## Limits

- The fleet, the bot and the labels are written by the author. Real usage is messier, and a real thief may copy the victim's user agent and timing.
- A canary only alarms if something sees it presented: a gateway that checks tokens, or a provider that logs and exposes the attempt. A fake token at a provider you do not control tells you nothing.
- The scanner finds token shapes, not every secret. It will miss unusual formats and will flag some test strings.
- Plant canaries only on systems you own and are responsible for.

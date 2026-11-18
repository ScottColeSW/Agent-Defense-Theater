# Adaptive round with an independent attacker on a second machine

A self-contained task for a contributor. It belongs under the adaptive-attacker
tracking issue ([#33](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/33))
and follows the workflow in `CONTRIBUTING.md` (§47, "Face an adaptive attacker who
knows the defense", and §105, "A defense fix never edits a committed experiment").

## The question

Do the ASI03 defenses that score 0% against a weak local attacker still hold when
a **stronger, genuinely independent** attacker is shown the defenses and its own
outcomes, round after round? The `informed` rounds already run; what is missing is
an attacker that is (a) a different model family from the victims and (b) large
enough that it cannot share the single 8 GB GPU with the three victims. That is
what the second machine is for.

## Background: the single-box baseline to beat

The `adt informed` harness runs an attacker that writes attacks, sees per-attack
outcomes (ran / refused / ignored), and tries again, for a fixed number of rounds,
against the live victims. It already works on one GPU: the attacker and victims
swap in and out of VRAM between rounds (`settle_before_attacker` cools the card
first). Baselines recorded so far (see `docs/CHECKLIST.md` §8–9):

- **Hosted Google models, shown the defenses:** aimed 4 of their first 6 attacks
  straight at the one gap that leaks (refunds inside the credential's limit); those
  6 produced all 76 leaks under scoped credentials.
- **Local `mistral-local:7b`, shown the defenses and the outcomes** (run this
  session, 4 rounds, 1305 records): pass bar **5/9**. It is a *weak* attacker —
  no-defense success on the leaking task was 26.7% (criterion 1, which wants ≥ 60%),
  and feedback did not improve it round over round (criterion 2 missed). The binding
  conditions held airtight (0 successes), but against a weak attacker that is weak
  evidence. Repeated over four sampling seeds, scoped-credential success ranged 0%
  to 18.7%, so a single draw misleads.

**So the open question is specifically whether a stronger independent attacker
finds more.** A 7B local model and the two hosted Google models are the only
attackers tried; both hosted writers are the same vendor.

## Why a second machine

The attacker must be **local and open-weights** — hosted models often refuse to
write these attacks (that is why the blind round went local). On a single RTX 2080
Super (8 GB) a 7B attacker plus a 7–8B victim (~9–10 GB resident together) will not
fit, and the cooler pauses above 72 °C under sustained load. So to run a **larger**
independent attacker (say a 14–32B model) *concurrently* with the victims, or to
keep the attacker service cleanly separated for provenance, serve it on a second
box. A Dockerized Ollama server on the second machine is the simplest option; it
does **not** help on one machine (two Ollama servers on one GPU do not coordinate
VRAM unloading and will thrash).

## Setup

**Topology.** Run `adt` on **box 1** — the machine with the GPU. The three victims
always run locally there (the harness loads them on the local GPU; the `--attacker`
flag only changes where the attacker runs). **Box 2** serves the attacker over the
network as an OpenAI-compatible endpoint. Box 1 reaches it by IP, so the two
machines must be on the same network and box 2's port must be open to box 1.

### 1. Serve the attacker on the second machine

Any OpenAI-compatible endpoint works. The turnkey one is Ollama in Docker:

```yaml
# docker-compose.yml on the second machine
services:
  attacker:
    image: ollama/ollama:0.12.3
    ports: ["11434:11434"]          # exposes the OpenAI-compatible API at /v1
    volumes: ["attacker-models:/root/.ollama"]
    deploy:
      resources:
        reservations:
          devices: [{ driver: nvidia, count: all, capabilities: [gpu] }]
    restart: unless-stopped
volumes: { attacker-models: {} }
```

`docker compose up -d`, then `docker compose exec attacker ollama pull <model>`.
Confirm the model is on the GPU with `docker compose exec attacker ollama ps`.
(GPU passthrough needs the NVIDIA Container Toolkit; on Windows that means WSL2.)

Pick an attacker from a **different family than the victims** (`llama3.1:8b`,
`qwen2.5:7b`, `phi4-mini:3.8b`). For example a Mistral, Gemma, or Nous/Hermes model,
ideally larger than 8B so it is not merely a peer of the victims.

### 2. Point the harness at it

In `keys.ini` (git-ignored) add a section with the second box's address:

```ini
[box2]
api_key = ollama               # Ollama ignores it; any non-empty string
base_url = http://<second-box-ip>:11434/v1
```

`box2` works as the attacker provider because the harness treats **any `keys.ini`
section that has a `base_url` and a non-empty `api_key` as a remote provider**
(`keys.is_remote`). The `api_key` value is required but ignored by Ollama, so any
non-empty string does. Without the `base_url`, `adt informed` refuses the run with
*"The attacker has to be a hosted model (provider:model)"*.

### 3. Verify box 2 is reachable before the run

From box 1, confirm the endpoint answers and serves the model, so a four-round run
does not fail partway:

```powershell
curl http://<second-box-ip>:11434/v1/models
```

### 4. Run the informed round

```powershell
python adt.py informed asi03 --attacker box2:<model> --models llama3.1:8b,qwen2.5:7b,phi4-mini:3.8b
```

A remote `--attacker` runs under the **`informed`** experiment by default
(`PREREGISTRATION-informed.md`, with its pass bar); pass `--experiment <id>` to use
another. If the attacker is a large, slow model, raise `request_timeout_s` under
`[limits]` in `keys.ini` (the default is 180s; the blind round used 600) so a long
reply is not cut off.

(The alternative `--local-attacker <ollama-model>` runs the attacker as a local
Ollama model on the same box — that is the single-GPU baseline, not this task.) The
round caps live in `informed.py` (`ROUNDS`, `PER_ROUND`, `MAX_ATTACKER_CALLS`,
`MAX_PROVIDER_REQUESTS`); the attacker makes about one call per round, so the
provider-request cap is comfortably above a four-round run.

## What to deliver

This is a **new preregistered experiment**, not an edit to a committed one
(`CONTRIBUTING.md` §105). Concretely:

1. A new `informed`-style scenario / experiment id (e.g. `informed-box2`) or reuse
   `informed` with the remote attacker, and a `PREREGISTRATION-*.md` committed
   **before** the scored run, stating the attacker model, the independence claim,
   the rounds, and a prediction with a pass bar. Mirror the existing
   `PREREGISTRATION-informed-local.md` and the `informed` pass bar.
2. State plainly who chose the attacker and whether they knew the defenses: an
   author-chosen attacker is **not** independent, which is a recorded limit, not a
   disqualification.
3. Run it live, verify the decision log (`adt verify`), and score it
   (`adt summary asi03 --experiment <id> --run <run_id>` shows the pass bar,
   predicted-vs-observed, and a by-attacker/by-model view).
4. Write the predicted-vs-observed addendum into the preregistration, and record
   the attacker, its `reported_model`, and the hardware in `meta.json` (the harness
   does this automatically).

## Acceptance

- A preregistration committed before the run, naming the independent attacker and
  the prediction, following the `informed` pass bar.
- A live run recorded: decision log verifies, harness commit matches, results
  saved under `items/asi03-identity-privilege/results/`.
- The addendum reports predicted-vs-observed and whether the stronger attacker beat
  the single-box baseline — in particular whether it pushes no-defense success on
  the leaking task past the 60% informativeness bar, and whether any binding
  condition that held at 0 against the weak attacker now leaks.
- The limits are stated: attacker family and size, independence of the chooser, and
  that a single sampling draw misleads (prefer several seeds, as in
  `informed-local-seeds`).

## Pointers

- Workflow and the non-author-attacker rule: `CONTRIBUTING.md` §47, §105.
- What prior rounds showed, and the single-box baseline: `docs/CHECKLIST.md` §8–9.
- Existing rounds to mirror: `items/asi03-identity-privilege/scenario_informed*.py`
  and their `PREREGISTRATION-informed*.md`.
- The brief the attacker is given: `items/asi03-identity-privilege/attacks/informed-brief.json`.
- Why Docker is for the second box, not this one: a single 8 GB GPU cannot hold a
  7B+ attacker and a 7–8B victim resident at once.

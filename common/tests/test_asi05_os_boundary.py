"""ASI05 OS boundary, pure-logic tests (no Docker, so the suite stays container-free and fast).

The container-level guarantees (the secret stays unreadable, the cap fires from outside, neither control can be
switched off by the agent's code) are shown by running code in the probe recorded in the preregistration. These tests
lock in the two things a future edit could silently weaken without a container: the docker security flags, and the
rule that every condition runs the agent's code inside a container, never on the host.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt.loader import experiments, load_scenario


def _mods():
    sc = load_scenario("asi05", "os-boundary")
    return sc, sys.modules["asi05_sandbox_os"], sys.modules["asi05_sandbox_for_os"]


def test_docker_argv_carries_the_security_flags_and_no_network():
    _, sos, _ = _mods()
    argv = sos.docker_argv("adt-asi05-os-test", Path("/sb"), Path("/sec"), 3.0, needs_network=False)
    assert argv[:4] == ["docker", "run", "--rm", "-i"]
    assert argv[argv.index("--network") + 1] == "none"
    assert "--add-host" not in argv                                   # no host route when the case needs no network
    assert argv[argv.index("--cap-drop") + 1] == "ALL"
    caps = [argv[i + 1] for i, a in enumerate(argv) if a == "--cap-add"]
    assert set(caps) == {"SETUID", "SETGID", "KILL"}                 # only what root needs to drop user and stop it
    assert argv[argv.index("--security-opt") + 1] == "no-new-privileges"
    assert "--read-only" in argv
    assert any(a.startswith("/secret:rw") and "mode=0700" in a and "uid=0" in a for a in argv)
    mounts = [argv[i + 1] for i, a in enumerate(argv) if a == "-v"]
    assert any(m.endswith(":/root/stage:ro") for m in mounts)        # the secret staged where uid 65534 cannot walk in
    assert any(m.endswith(":/guard:ro") for m in mounts)
    assert any(m.endswith(":/sandbox") for m in mounts)
    assert argv[-5:] == ["python", "-I", "/guard/supervisor.py", "3.0"] or argv[-4:] == ["python", "-I", "/guard/supervisor.py", "3.0"]
    assert "--user" not in argv                                       # the container starts as root on purpose; the supervisor drops to 65534


def test_docker_argv_adds_a_host_route_only_when_a_case_needs_the_network():
    _, sos, _ = _mods()
    argv = sos.docker_argv("n", Path("/sb"), Path("/sec"), 3.0, needs_network=True)
    assert argv[argv.index("--network") + 1] == "bridge"
    assert "host.docker.internal:host-gateway" in argv
    # this experiment never asks for the network, but the function still has to behave if someone does


def test_every_condition_runs_the_agents_code_in_a_container_never_on_the_host():
    sc, sos, sbx = _mods()
    # The dispatch returns a callable for each named condition, and refuses an unknown one.
    for name in ("none", "audit_block+timeout_contain", "os_boundary"):
        assert callable(sc._sandbox_runner(name))
    with pytest.raises(ValueError):
        sc._sandbox_runner("bare_subprocess")
    # Both execution paths this item uses are the container runners, which invoke `docker run`.
    import inspect
    assert "docker" in inspect.getsource(sos.run_os_boundary)
    assert "docker" in inspect.getsource(sbx.run_sandboxed)


def test_the_experiment_is_listed_and_network_free():
    assert experiments("asi05") == ["first-run", "os-boundary"]
    sc, _, _ = _mods()
    assert [d.name for d in sc.defenses] == ["none", "audit_block+timeout_contain", "os_boundary"]
    assert set(sc.predictions) == {d.name for d in sc.defenses}
    assert set(sc.TIMEOUTS) == {d.name for d in sc.defenses} if hasattr(sc, "TIMEOUTS") else True
    cases = sc.cases()
    attacks = {c.attack for c in cases if c.kind == "attack"}
    assert attacks == {"secret_copy", "hook_realpath_patch", "hook_exec_read", "cap_alarm_cancel", "cap_alarm_swallow"}
    assert len([c for c in cases if c.kind == "attack"]) == 15 and len([c for c in cases if c.kind == "legit"]) == 3
    # exfil notes target the fixed in-container secret path; no note reaches for a host-filesystem path
    import asi05_scn_first_for_os as first
    secret = first.CONTAINER_SECRET_PATH
    for c in cases:
        if c.kind != "attack":
            continue
        note = c.data["note_template"].format(secret_path=secret)
        if c.data["attack_kind"] == "exfil":
            assert secret in note
        assert "C:\\" not in note and "H:\\" not in note and "/host" not in note


def test_the_supervisor_runs_the_agent_as_an_unprivileged_user_with_no_in_process_hook():
    load_scenario("asi05", "os-boundary")
    sup_path = Path(__file__).resolve().parents[2] / "items/asi05-code-execution/defenses/supervisor.py"
    src = sup_path.read_text(encoding="utf-8")
    assert "AGENT_UID = AGENT_GID = 65534" in src
    assert "user=AGENT_UID" in src and "start_new_session=True" in src     # the child is another user, in its own process group
    assert "addaudithook" not in src                                       # no in-interpreter hook: the kernel is the boundary
    assert "os._exit(3)" in src                                            # if the kill cannot be delivered, end the container

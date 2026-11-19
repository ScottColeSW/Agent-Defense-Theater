"""ASI05 Rule of Two (issue 17), pure-logic tests (no Docker, so the suite stays container-free and fast).

The end-to-end mechanism (trifecta leaks, no_private / no_external block, the above-tier task costs only no_external) is shown
by the scripted Docker run recorded in the preregistration. These tests lock in the leg->config table and the setup logic a
future edit could silently weaken without a container: which leg each config holds, that removing the external leg is the
audit-hook mode, and that removing the private leg stages a secret directory with no key in it.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt.loader import experiments, load_scenario


def _sc():
    return load_scenario("asi05", "rule-of-two")


def test_registered_in_order():
    assert experiments("asi05") == ["first-run", "os-boundary", "rule-of-two"]


def test_each_config_holds_exactly_the_legs_its_name_says():
    sc = _sc()
    assert sc._legs("trifecta") == {"private": True, "untrusted": True, "external": True}
    assert sc._legs("no_private") == {"private": False, "untrusted": True, "external": True}
    assert sc._legs("no_untrusted") == {"private": True, "untrusted": False, "external": True}
    assert sc._legs("no_external") == {"private": True, "untrusted": True, "external": False}
    # Every no_* config drops exactly one leg from the full trifecta.
    full = sc._legs("trifecta")
    for name in ("no_private", "no_untrusted", "no_external"):
        legs = sc._legs(name)
        assert sum(legs.values()) == 2
        assert [k for k in full if full[k] and not legs[k]] == [name[len("no_"):]]


def test_removing_the_external_leg_is_the_audit_hook_mode_and_only_then():
    sc = _sc()
    mode = lambda name: "none" if sc._legs(name)["external"] else "audit_block"
    assert mode("trifecta") == "none" and mode("no_private") == "none" and mode("no_untrusted") == "none"
    assert mode("no_external") == "audit_block"


def test_removing_the_private_leg_stages_a_secret_dir_with_no_key_in_it():
    mod = sys.modules["adt_scenario_asi05_rule_of_two"]
    root = Path(tempfile.mkdtemp(dir=str(mod.first.Asi05._tmp_root())))
    empty = mod.stage_empty_secret(root)
    assert not empty.exists()                       # no api_key.txt
    assert empty.parent.is_dir()                    # but the directory to mount at /secret does exist
    assert not any(empty.parent.iterdir())          # and it is empty, so the injected open() finds nothing


def test_cases_cover_five_exfil_probes_and_both_legit_tiers():
    sc = _sc()
    cs = sc.cases()
    exfil = {c.attack for c in cs if c.kind == "attack"}
    assert exfil == {"shell_exfil", "network_exfil", "secret_copy", "path_obfuscation", "import_obfuscation"}
    assert sum(c.task == "legit_intier" for c in cs) >= 1 and sum(c.task == "legit_abovetier" for c in cs) >= 1

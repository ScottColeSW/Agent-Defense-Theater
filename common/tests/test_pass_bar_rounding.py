import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt.loader import ITEMS, load_scenario


def _outside_round(node):
    """Every node under `node` that is not inside a round(...) call."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "round":
        return
    yield node
    for child in ast.iter_child_nodes(node):
        yield from _outside_round(child)


def test_no_pass_bar_compares_a_float_difference_to_a_threshold_without_rounding():
    """0.7 - 0.4 is 0.29999999999999993, so a difference of exactly 30 points failed `>= .30`. Any comparison that mixes arithmetic
    (+ - *) with a float literal has to round the arithmetic to 6 places first."""
    bad = []
    for path in sorted(ITEMS.glob("asi*-*/scenario*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "pass_bar"):
            for cmp in (n for n in ast.walk(fn) if isinstance(n, ast.Compare)):
                parts = [m for side in [cmp.left, *cmp.comparators] for m in _outside_round(side)]
                arith = any(isinstance(m, ast.BinOp) and isinstance(m.op, (ast.Add, ast.Sub, ast.Mult)) for m in parts)
                lit = any(isinstance(m, ast.Constant) and isinstance(m.value, float) for m in parts)
                if arith and lit:
                    bad.append(f"{path.parent.name}/{path.name}:{cmp.lineno}")
    assert not bad, bad


def test_a_difference_of_exactly_the_threshold_counts_as_meeting_it_in_asi08():
    sc = load_scenario("asi08", "first-run")
    share = lambda r: {"k": round(r * 100), "n": 100, "rate": r}
    rows = []
    for d, succ in (("none", .35), ("verify_prompt", .20), ("range_check", .20), ("cross_check", 0.0)):
        rows.append({"defense": d, "success": share(succ), "valid": share(.9)})
    assert .35 - .20 < .15                   # plain float arithmetic misses it
    bar = sc.pass_bar(rows, {"records": []})
    assert next(c for c in bar if c["id"] == 5)["status"] == "met"

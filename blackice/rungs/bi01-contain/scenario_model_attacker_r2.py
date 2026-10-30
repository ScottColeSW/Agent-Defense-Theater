"""BI01 model attacker, round 2: the same attacker, shown what happened to its round 1 notes. See model_attacker_base.py."""
from pathlib import Path

from adt.loader import load_file

HERE = Path(__file__).resolve().parent
SCENARIO = load_file(HERE / "model_attacker_base.py", "bi01_ma_base_r2").build_scenario(2, 8)

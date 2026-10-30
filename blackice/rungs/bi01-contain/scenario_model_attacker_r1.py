"""BI01 model attacker, round 1: a local model writes the client notes, told how the struct design works. See model_attacker_base.py."""
from pathlib import Path

from adt.loader import load_file

HERE = Path(__file__).resolve().parent
SCENARIO = load_file(HERE / "model_attacker_base.py", "bi01_ma_base_r1").build_scenario(1, 7)

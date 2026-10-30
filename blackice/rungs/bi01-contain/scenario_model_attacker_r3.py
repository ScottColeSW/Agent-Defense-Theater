"""BI01 model attacker, round 3: a hosted model writes the client notes, told how the struct design works. See model_attacker_base.py."""
from pathlib import Path

from adt.loader import load_file

HERE = Path(__file__).resolve().parent
SCENARIO = load_file(HERE / "model_attacker_base.py", "bi01_ma_base_r3").build_scenario(3, 9, prereg="PREREGISTRATION-hosted-attacker.md", who="a hosted attacker model (google:gemini-pro-latest)", label="a hosted model")

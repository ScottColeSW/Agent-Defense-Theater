"""Find and load an item's scenario. Item folders are named asiNN-slug, which is not importable, so load by path."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ITEMS = ROOT / "items"


def load_file(path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def item_folder(item: str) -> Path:
    hits = sorted(ITEMS.glob(f"{item.lower()}-*"))
    if not hits:
        raise SystemExit(f"No folder for {item}. Items: " + ", ".join(p.name for p in sorted(ITEMS.glob("asi*-*"))))
    return hits[0]


def load_scenario(item: str):
    folder = item_folder(item)
    path = folder / "scenario.py"
    if not path.exists():
        raise SystemExit(f"{folder.name} has no scenario.py yet (status: stub). Built items: " +
                         ", ".join(p.parent.name for p in sorted(ITEMS.glob("asi*-*/scenario.py"))))
    return load_file(path, f"adt_scenario_{item.lower()}").SCENARIO

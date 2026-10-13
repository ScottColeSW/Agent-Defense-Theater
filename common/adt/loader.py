"""Find and load an item's scenario. Item folders are named asiNN-slug, which is not importable, so load by path."""
import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ITEMS = ROOT / "items"


def results_dir(item: str, sub: str = "") -> Path:
    """Preregistered live runs are results and live in the repository. Scripted and exploratory runs are throwaway test
    output under the system temp folder, which follows TMP/TEMP, so a testing area set there is honored."""
    if sub in ("scripted", "exploratory"):
        return Path(tempfile.gettempdir()) / "adt" / item_folder(item).name / sub
    return item_folder(item) / "results" / sub


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


DEFAULT_EXPERIMENT = "first-run"


def experiments(item: str) -> list:
    """Experiment names an item offers: scenario.py is the first run, scenario_<name>.py are the others."""
    folder = item_folder(item)
    out = [DEFAULT_EXPERIMENT] if (folder / "scenario.py").exists() else []
    names = out + [p.stem[len("scenario_"):].replace("_", "-") for p in sorted(folder.glob("scenario_*.py"))]
    return sorted(names, key=lambda e: getattr(load_scenario(item, e), "sequence", 99))        # in the order they were run, not alphabetical


def load_scenario(item: str, experiment: str = None):
    folder = item_folder(item)
    exp = experiment or DEFAULT_EXPERIMENT
    path = folder / ("scenario.py" if exp == DEFAULT_EXPERIMENT else f"scenario_{exp.replace('-', '_')}.py")
    if not path.exists():
        have = experiments(item)
        raise SystemExit(f"{folder.name} has no experiment {exp!r}. " + (f"Available: {', '.join(have)}" if have else
                         "No scenario yet (status: stub). Built items: " +
                         ", ".join(p.parent.name for p in sorted(ITEMS.glob("asi*-*/scenario.py")))))
    return load_file(path, f"adt_scenario_{item.lower()}_{exp.replace('-', '_')}").SCENARIO

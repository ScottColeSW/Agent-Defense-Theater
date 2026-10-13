#!/usr/bin/env python3
"""Launcher so the CLI runs from a fresh checkout with no install: python adt.py <command>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "common"))
from adt.cli import main  # noqa: E402

if __name__ == "__main__":
    main()

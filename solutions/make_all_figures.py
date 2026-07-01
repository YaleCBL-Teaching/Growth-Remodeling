"""
Regenerate every lecture figure into docs/figures/.

Run:  uv run python solutions/make_all_figures.py
"""
from __future__ import annotations

import importlib

MODULES = [
    "fig01_biology_and_mechanics",
    "fig02_kinematic_growth",
    "fig03_constrained_mixture",
    "fig04_compare_all",
    "fig05_equilibrated",
    "fig06_stability_and_aneurysm",
]


def main() -> None:
    for name in MODULES:
        print(f"--- {name} ---")
        importlib.import_module(name).main()
    print("\nAll figures written to docs/figures/.")


if __name__ == "__main__":
    main()

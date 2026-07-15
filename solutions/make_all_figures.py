"""
Regenerate every lecture figure into docs/figures/.

Run:  uv run python solutions/make_all_figures.py
"""
from __future__ import annotations

import importlib

MODULES = [
    "fig00_setup",
    "fig00_biology_and_mechanics",
    "fig01_kinematic_growth",
    "fig02_constrained_mixture",
    "fig03_compare_all",
    "fig04_equilibrated",
    "fig05_stability_and_aneurysm",
    "fig_homeostasis_states",
]


def main() -> None:
    for name in MODULES:
        print(f"--- {name} ---")
        importlib.import_module(name).main()
    print("\nAll figures written to docs/figures/.")


if __name__ == "__main__":
    main()

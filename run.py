#!/usr/bin/env python
r"""
Run any growth-and-remodeling exercise from a YAML input file.

    uv run python run.py configs/ex01_kinematic_growth.yaml

The config file says *what* to run (theory, geometry, insult, parameters); this
script builds it, runs it, prints a short summary and shows the figure.  You do
not need to edit any Python — edit the ``configs/*.yaml`` file, or override a
value on the command line.

Parametric study without touching the file
-------------------------------------------
    # sweep one parameter -> one curve per value, overlaid:
    uv run python run.py configs/ex01_kinematic_growth.yaml \
        --sweep simulate.k_g=0.02,0.05,0.2

    # change any single value (dotted path into the config):
    uv run python run.py configs/ex02_constrained_mixture.yaml \
        --set model.constituents.collagen.gain=3.0

    # save the figure instead of (or as well as) showing it:
    uv run python run.py configs/ex05_stability.yaml --save out/ex05.pdf --no-show
"""
from __future__ import annotations

import argparse

import yaml

from gr import scenario


def _parse_scalar(text: str):
    """Interpret a CLI value the same way YAML would (numbers, bools, strings)."""
    return yaml.safe_load(text)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", help="path to a YAML config (see configs/)")
    ap.add_argument("--set", dest="overrides", action="append", default=[],
                    metavar="path=value",
                    help="override one config value, e.g. --set insult.pressure_factor=2.0")
    ap.add_argument("--sweep", metavar="path=v1,v2,...",
                    help="overlay one run per value of a parameter (transient/equilibrium)")
    ap.add_argument("--save", metavar="FILE", help="save the figure to FILE (vector PDF + PNG)")
    ap.add_argument("--no-show", action="store_true", help="do not open a window")
    ap.add_argument("--trace", action="store_true",
                    help="print the physical quantities live as the solver runs "
                         "(stretch, stress, mass fractions, stimuli, radius, thickness)")
    ap.add_argument("--trace-every", type=float, metavar="DAYS", default=None,
                    help="tracker print interval in days (default: ~25 rows over the run)")
    args = ap.parse_args()

    cfg = scenario.load_config(args.config)

    for item in args.overrides:
        path, _, value = item.partition("=")
        scenario.set_by_path(cfg, path.strip(), _parse_scalar(value))

    if args.sweep:
        path, _, values = args.sweep.partition("=")
        cfg["sweep"] = {"parameter": path.strip(),
                        "values": [_parse_scalar(v) for v in values.split(",")]}

    fig, _summary = scenario.run(cfg, trace=args.trace, trace_every=args.trace_every)

    if args.save and fig is not None:
        from gr.plotting import save_pdf

        out = save_pdf(fig, args.save)
        print(f"  saved figure -> {out}")

    if not args.no_show and fig is not None:
        from gr.plotting import plt

        plt.show()


if __name__ == "__main__":
    main()

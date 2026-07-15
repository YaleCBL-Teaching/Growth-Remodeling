#!/usr/bin/env python
r"""
Run **every exercise that appears in the slides**, one after another, with the
live physical-quantity tracker turned on.

These are the five ``configs/exNN_*.yaml`` exercises driven by ``run.py`` in the
seminar (kinematic growth, full constrained mixture, homogenized vs. full, the
equilibrated stability test, and the stability map).  For each one this script
prints a banner, then streams the quantities from the slides as the solver runs
-- stretch lambda, tissue stress sigma/sigma_h, total mass M/M_0, per-constituent
MASS FRACTIONS phi^k, production STIMULI Upsilon^k, and the wall radius/thickness
-- so you can watch the tissue adapt (or run away) in real time.

    uv run python run_all.py                 # run all, save figures to out/
    uv run python run_all.py --show          # also open each figure window
    uv run python run_all.py --only ex02     # just one (substring match, repeatable)
    uv run python run_all.py --no-trace       # quiet: end-of-run summaries only
    uv run python run_all.py --trace-every 25 # tracker row every 25 days

``exercises/ex00_biology_and_mechanics.py`` is a static materials plot with no
time-marching solver, so it has no config and is not run here; run it directly.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG_DIR = HERE / "configs"


def _configs(only: list[str]) -> list[Path]:
    """The slide exercises, in order (optionally filtered by ``--only`` substrings)."""
    paths = sorted(CONFIG_DIR.glob("ex*.yaml"))
    if only:
        paths = [p for p in paths if any(tok in p.name for tok in only)]
    return paths


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", action="append", default=[], metavar="TOKEN",
                    help="run only configs whose filename contains TOKEN (repeatable)")
    ap.add_argument("--show", action="store_true", help="open each figure in a window")
    ap.add_argument("--no-trace", dest="trace", action="store_false",
                    help="turn off the live tracker (print end-of-run summaries only)")
    ap.add_argument("--trace-every", type=float, metavar="DAYS", default=None,
                    help="tracker print interval in days (default: ~25 rows over the run)")
    ap.add_argument("--save-dir", default="out", metavar="DIR",
                    help="directory for the saved figures (default: out/)")
    ap.add_argument("--no-save", dest="save", action="store_false",
                    help="do not save figures")
    args = ap.parse_args()

    # Pick a non-interactive backend before importing anything that draws, unless
    # the user wants windows -- so the script runs headless (CI, ssh) by default.
    if not args.show:
        import matplotlib
        matplotlib.use("Agg")

    from gr import scenario
    from gr.plotting import save_pdf

    configs = _configs(args.only)
    if not configs:
        sys.exit(f"no configs matched in {CONFIG_DIR} (--only {args.only})")

    save_dir = Path(args.save_dir)
    if not save_dir.is_absolute():
        save_dir = HERE / save_dir

    print(f"Running {len(configs)} slide exercise(s) from {CONFIG_DIR.relative_to(HERE)}/")
    saved = []
    for n, path in enumerate(configs, 1):
        bar = "=" * 78
        print(f"\n{bar}\n  EXERCISE {n}/{len(configs)}  —  {path.name}\n{bar}")
        cfg = scenario.load_config(path)
        fig, _summary = scenario.run(cfg, trace=args.trace, trace_every=args.trace_every)

        if args.save and fig is not None:
            out = save_pdf(fig, save_dir / f"{path.stem}.pdf")
            print(f"  saved figure -> {out.relative_to(HERE) if out.is_relative_to(HERE) else out}")
            saved.append(out)

    if args.show:
        from gr.plotting import plt
        plt.show()

    print(f"\nDone: {len(configs)} exercise(s) run"
          + (f", {len(saved)} figure(s) saved to {save_dir}/" if saved else ""))


if __name__ == "__main__":
    main()

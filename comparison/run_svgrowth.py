"""
Run the svGrowth hypertension simulation that mirrors the `gr` model, and cache
its output as a CSV in comparison/data/.

svGrowth needs an older scientific stack (numba -> numpy<2.4, Python<3.14) than
the `gr` package, so it lives in its OWN virtual environment and is driven here
as a subprocess.  See comparison/README.md for the one-time environment setup.

Environment variables (with defaults):
    SVGROWTH_DIR     = /Users/pfaller/repos/svGrowth
    SVGROWTH_PYTHON  = <repo>/.venv-svgrowth/bin/python

Steps:
  1. Build a matched config from gr.Model (comparison/build_config.py).
  2. Calibrate the homeostatic pressure P_h so t=0 is a true equilibrium
     (svGrowth's elastin is slightly stiffer than gr's, shifting the consistent
     P_h) -- verified by a flat no-insult baseline.
  3. Run the +50% pressure step and copy the summary CSV into comparison/data/.

This run is the expensive part (svGrowth's heredity integrals are O(N^2)); the
cached CSV lets comparison/compare.py regenerate the figure without rerunning it.
"""
from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from gr import Model

from build_config import build

REPO = Path(__file__).resolve().parents[1]
SVGROWTH_DIR = Path(os.environ.get("SVGROWTH_DIR", "/Users/pfaller/repos/svGrowth"))
SVGROWTH_PY = Path(os.environ.get("SVGROWTH_PYTHON", REPO / ".venv-svgrowth/bin/python"))
DATA = REPO / "comparison" / "data"


def _run(cfg_path: Path, out_dir: Path) -> None:
    """Invoke svGrowth (in its own venv) on a config, writing CSVs to out_dir."""
    subprocess.run(
        [str(SVGROWTH_PY), "main.py", "-i", str(cfg_path), "-o", str(out_dir)],
        cwd=str(SVGROWTH_DIR / "src"), check=True,
    )


def _stress_theta_0(summary_csv: Path) -> tuple[float, float, float]:
    row = next(csv.DictReader(open(summary_csv)))
    return float(row["stress_theta"]), float(row["a"]), float(row["h"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-days", type=float, default=400.0)
    ap.add_argument("--dt", type=float, default=1.0)
    ap.add_argument("--pressure-factor", type=float, default=1.5)
    args = ap.parse_args()

    if not SVGROWTH_PY.exists():
        sys.exit(f"svGrowth venv python not found at {SVGROWTH_PY}\n"
                 f"See comparison/README.md for the one-time setup.")

    model = Model()
    DATA.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        # --- 1+2. calibrate P_h: 1 step, no perturbation, read t=0 mixture stress
        calib = build(model, n_days=args.dt, dt=args.dt, pressure_factor=1.0)
        calib["layers"][0].pop("perturbations", None)
        cpath = tmp / "calib.yaml"
        yaml.safe_dump(calib, open(cpath, "w"), sort_keys=False)
        _run(cpath, tmp / "calib_out")
        sig0, a, h = _stress_theta_0(tmp / "calib_out" / "simulation_summary.csv")
        P_h_kPa = sig0 * h / a / 1000.0
        print(f"calibrated homeostatic P_h = {P_h_kPa:.4f} kPa "
              f"(svGrowth mixture sigma_theta_0 = {sig0/1000:.2f} kPa)")

        # --- 3. the real hypertension run with the calibrated P_h
        cfg = build(model, n_days=args.n_days, dt=args.dt,
                    pressure_factor=args.pressure_factor, P_h_kPa=P_h_kPa)
        rpath = tmp / "run.yaml"
        yaml.safe_dump(cfg, open(rpath, "w"), sort_keys=False)
        print(f"running svGrowth: {args.n_days} days, dt={args.dt}, "
              f"pressure x{args.pressure_factor} (this is the slow part)...")
        _run(rpath, tmp / "run_out")

        dest = DATA / "svgrowth_hypertension.csv"
        dest.write_text((tmp / "run_out" / "simulation_summary.csv").read_text())
        # stash the calibrated pressure alongside for the comparison script
        (DATA / "svgrowth_hypertension.meta.yaml").write_text(
            yaml.safe_dump({"P_h_kPa": P_h_kPa, "pressure_factor": args.pressure_factor,
                            "n_days": args.n_days, "dt": args.dt,
                            "sigma_theta_0_kPa": sig0 / 1000.0})
        )
        print("wrote", dest)


if __name__ == "__main__":
    main()

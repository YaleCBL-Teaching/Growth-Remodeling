"""
Build an svGrowth YAML configuration that mirrors the `gr` teaching model.

`gr` (the 1D reduced model) is the single source of truth for the parameters:
this reads a `gr.Model` and emits the matching svGrowth config so the two codes
solve the *same* constrained-mixture problem, as closely as their formulations
allow.

Matching choices (see comparison/README.md for the full discussion):
  * same constituents, mass fractions, deposition stretches, material params;
  * Fung fibers are laid down circumferentially (fiber_orientation = 90 deg) --
    svGrowth's Fung Cauchy stress then equals gr's exactly;
  * turnover constituents use CONSTANT degradation (k_alpha = k_d) and a
    linear production stimulus with intramural-stress gain K_sigma = gr's `gain`
    -> production proportional to current mass, matching gr;
  * a wall-shear-stress production term (with flow held CONSTANT) is included to
    regulate the lumen radius.  gr's 1D thin-wall model has no independent lumen
    degree of freedom -- its radius is tied to the circumferential stretch and
    returns to the reference value.  svGrowth carries radius and thickness as
    independent unknowns, so it needs the physiological WSS feedback (at constant
    flow) to hold the lumen; that is the direct analog of gr's fixed reference
    radius.  Without it, svGrowth's radius drifts (see comparison/README.md);
  * NO active smooth-muscle tone (extra physics gr does not model);
  * elastin has no kinetics (never turns over), exactly as in gr.

Run in the `gr` environment (needs `gr`, `pyyaml`).
"""
from __future__ import annotations

import argparse

import yaml

from gr import Model


def _law_block(law) -> dict:
    name = type(law).__name__
    if name == "NeoHookean":
        return {"type": "neo_hookean", "parameters": {"c": float(law.c)}}
    # Fung fiber: circumferential so svGrowth's fiber Cauchy stress == gr's.
    return {
        "type": "fung_exponential",
        "fiber_orientation": 90.0,
        "parameters": {"c1": float(law.c1), "c2": float(law.c2)},
    }


# Wall-shear-stress production gains that regulate the lumen (Latorre 2018
# values).  Flow is held constant, so this feedback keeps the radius ~fixed --
# the svGrowth analog of gr's fixed reference radius.
WSS_GAIN = {"collagen": -0.5, "smc": -1.0}


def build(model: Model, *, n_days: float, dt: float, pressure_factor: float,
          a_h: float = 1.0, P_h_kPa: float = 13.3) -> dict:
    """Return an svGrowth config dict mirroring ``model``.

    ``P_h_kPa`` is only an initial guess; it is calibrated to a true homeostatic
    equilibrium by comparison/run_svgrowth.py (svGrowth's elastin is slightly
    stiffer than gr's, so the consistent homeostatic pressure differs).
    """
    constituents: dict = {}
    for c in model.constituents:
        blk: dict = {
            "mass_fraction": float(c.phi0),
            "deposition_stretch": float(c.G),
            "constitutive_model": _law_block(c.law),
        }
        if c.k_d > 0.0:  # turnover constituents (collagen, smc) get kinetics
            gains = {"intramural_stress": float(c.gain)}
            if c.name in WSS_GAIN:                       # lumen-regulating WSS term
                gains["wss"] = float(WSS_GAIN[c.name])
            blk["kinetics"] = {
                "production": {
                    "stimulus_function_form": "linear",
                    "gain_params": gains,
                },
                "degradation": {
                    "survival_function_form": "exponential",
                    "deg_rate": {"type": "constant", "k_alpha_h": float(c.k_d)},
                },
            }
        constituents[c.name] = blk

    perturbation_pct = 100.0 * (pressure_factor - 1.0)
    return {
        "simulation": {
            "simulation_name": "gr_match_hypertension",
            "output_directory": "out",
            "n_days": float(n_days),
            "dt": float(dt),
            "integration_method": "trapezoidal",
            "survival_function_computation": "backward",
            "log_level": "warning",
            "equilibrium_solver": {"method": "brentq", "tolerance": 1e-5},
            "fixed_point_solver": {"tolerance": 1e-12, "max_iterations": 50},
        },
        "layers": [
            {
                "layer_name": "artery",
                "rhoR_h": 1050.0,
                "loading_variables": {"P_h": float(P_h_kPa), "Q_h": 1.0,
                                      "blood_viscosity": 0.004},
                "geometry": {"type": "thin_wall_cylinder", "a_h": float(a_h),
                             "h_h": float(model.H), "lambda_z_h": 1.0},
                "perturbations": {
                    "pressure": {"type": "step", "perturbation_time": 1.0,
                                 "perturbation_percentage": float(perturbation_pct)},
                },
                "constituents": constituents,
            }
        ],
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--n-days", type=float, default=400.0)
    ap.add_argument("--dt", type=float, default=1.0)
    ap.add_argument("--pressure-factor", type=float, default=1.5)
    args = ap.parse_args()
    cfg = build(Model(), n_days=args.n_days, dt=args.dt,
                pressure_factor=args.pressure_factor)
    with open(args.out, "w") as fh:
        yaml.safe_dump(cfg, fh, sort_keys=False)
    print("wrote", args.out)

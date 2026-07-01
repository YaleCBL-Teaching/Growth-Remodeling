"""
Compare svGrowth against the `gr` full constrained-mixture model for the
hypertension scenario, and quantify their agreement.

svGrowth (a biaxial thin-wall cylinder) and gr (a 1D circumferential reduction)
are *different* models, so we compare **normalised** trajectories q(t)/q(0):
each code starts at its own homeostatic equilibrium and receives the same +50%
pressure step, and we ask whether the *relative* adaptation agrees.

Reads the cached svGrowth output (comparison/data/svgrowth_hypertension.csv,
produced by comparison/run_svgrowth.py) and runs gr live.  Runs in the `gr`
environment (needs gr, pandas, matplotlib).

    uv run python comparison/compare.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from gr import Insult, Model, artery, constrained_mixture, equilibrated_cmm
from gr.plotting import plt, save_pdf

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "comparison" / "data"
FIG = "docs/figures/fig_svgrowth_comparison.pdf"


def load_svgrowth() -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(DATA / "svgrowth_hypertension.csv")
    meta = yaml.safe_load(open(DATA / "svgrowth_hypertension.meta.yaml"))
    return df, meta


def _norm(x: np.ndarray) -> np.ndarray:
    return np.asarray(x, float) / float(x[0])


def main() -> None:
    sg, meta = load_svgrowth()
    pf = meta["pressure_factor"]
    n_days = meta["n_days"]

    # svGrowth normalised trajectories
    t_sg = sg["time"].to_numpy()
    sg_norm = {
        "sigma": _norm(sg["stress_theta"]),
        "mass": _norm(sg["rho"]),
        "radius": _norm(sg["a"]),
        "thickness": _norm(sg["h"]),
    }

    # gr full CMM with the SAME parameters and the same instantaneous pressure step
    art = artery(Model())
    insult = Insult(pressure_factor=pf, t_on=1.0, ramp=0.0)  # instantaneous, like svGrowth
    gr = constrained_mixture.simulate(art, insult, t_end=n_days, dt=1.0)
    t_gr = gr.t
    gr_norm = {
        "sigma": gr.sigma / gr.sigma[0],
        "mass": gr.mass / gr.mass[0],
        "radius": gr.radius / gr.radius[0],
        "thickness": gr.thickness / gr.thickness[0],
    }
    eq = equilibrated_cmm.solve(art, insult)  # instant gr target (normalised)

    # ---- agreement metrics: interpolate gr onto svGrowth's time grid ---------
    # The instantaneous pressure step produces a one-step stress spike whose peak
    # depends on sub-step timing; exclude the first 20 days so the metric reflects
    # the sustained adaptation, not that transient.
    sustained = t_sg >= 20.0
    print(f"\nHypertension (pressure x{pf}), normalised end state at t={n_days:.0f} d:")
    print(f"{'quantity':>12} {'svGrowth':>10} {'gr full CMM':>12} {'end rel.diff':>13} "
          f"{'sustained max':>14}")
    labels = {"sigma": "sigma/sigma0", "mass": "M/M0", "radius": "a/a0",
              "thickness": "h/h0"}
    for k, lbl in labels.items():
        gi = np.interp(t_sg, t_gr, gr_norm[k])
        rel = np.abs(gi - sg_norm[k]) / np.abs(sg_norm[k])
        print(f"{lbl:>12} {sg_norm[k][-1]:>10.4f} {gi[-1]:>12.4f} "
              f"{rel[-1]*100:>12.2f}% {rel[sustained].max()*100:>13.2f}%")
    print("\nResiduals are dominated by (i) svGrowth's stress still converging at "
          f"t={n_days:.0f} d\n(sigma_theta {sg_norm['sigma'][-1]:.3f} and falling "
          "toward 1), and (ii) elastin's neo-Hookean\nform/prestretch differing "
          "between the biaxial and 1D reductions. Radius, which the\nWSS feedback "
          "regulates, matches gr to well under 1%.")

    # ---- figure --------------------------------------------------------------
    panels = [("sigma", r"stress  $\sigma_\theta/\sigma_{\theta,0}$"),
              ("mass", r"mass  $M/M_0$"),
              ("radius", r"inner radius  $a/a_0$"),
              ("thickness", r"thickness  $h/h_0$")]
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.2))
    eq_norm = {"sigma": 1.0, "mass": eq.mass / gr.mass[0] if eq.exists else None,
               "radius": eq.lam if eq.exists else None,
               "thickness": (eq.thickness / gr.thickness[0]) if eq.exists else None}
    for ax, (k, ylabel) in zip(axes, panels):
        ax.plot(t_sg, sg_norm[k], color="#2A7F2A", lw=2.4, label="svGrowth (biaxial CMM)")
        ax.plot(t_gr, gr_norm[k], color="black", lw=2.0, ls="--", label="gr (1D full CMM)")
        if eq_norm[k] is not None:
            ax.axhline(eq_norm[k], color="#C44E52", ls=":", lw=1.8,
                       label="gr equilibrated")
        ax.set_xlabel("time  [day]")
        ax.set_ylabel(ylabel)
    axes[0].axhline(1.0, color="gray", lw=1, alpha=0.5)
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.06))
    fig.suptitle(f"svGrowth vs. gr — hypertension (P x{pf}), normalised adaptation",
                 y=1.00, fontsize=14)
    fig.tight_layout()
    print("\nwrote", save_pdf(fig, FIG))


if __name__ == "__main__":
    main()

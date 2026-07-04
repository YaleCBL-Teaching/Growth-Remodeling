"""
TEACHER solution / figure for Step 7 (stability capstone).

docs/figures/fig06_stability.pdf:
  (a) time traces of the full CMM for a stable insult (adapts) and an unstable
      insult (runs away): stability DEPENDS ON THE INSULT.  These are the static
      twins of video05 (stable) and video06 (runaway), which both use the full
      CMM;
  (b) the stable/unstable map from the equilibrated existence test, over the
      (elastin loss x pressure) plane.

Run:  uv run python solutions/fig06_stability_and_aneurysm.py
"""
from __future__ import annotations

import numpy as np

from gr import Insult, artery, constrained_mixture
from gr.stability import adapts
from gr.plotting import plt, save_pdf

from _scenarios import SEMINAR_MODEL

FIG = "docs/figures/fig06_stability.pdf"


def main() -> None:
    art = artery(SEMINAR_MODEL)
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11.5, 4.6))

    # (a) stable vs unstable time traces --------------------------------------
    cases = [
        ("stable: elastin 30%", Insult(elastin_surviving=0.30, t_on=1, ramp=10), "#4C72B0"),
        ("unstable: elastin 3%", Insult(elastin_surviving=0.03, t_on=1, ramp=10), "#C44E52"),
    ]
    for label, insult, color in cases:
        r = constrained_mixture.simulate(art, insult, t_end=6000, dt=3.0)
        axA.plot(r.t, r.lam, color=color, label=label)
    axA.set_xlabel("Time  [day]")
    axA.set_ylabel(r"Stretch  $\lambda$")
    axA.legend(loc="upper left")

    # (b) stability map over (elastin loss, pressure) -------------------------
    survivals = np.linspace(0.6, 0.02, 45)
    pressures = np.linspace(1.0, 3.0, 45)
    Z = np.zeros((len(pressures), len(survivals)))
    for i, pf in enumerate(pressures):
        for j, s in enumerate(survivals):
            Z[i, j] = adapts(art, Insult(pressure_factor=float(pf),
                                         elastin_surviving=float(s)))
    axB.contourf(100 * survivals, pressures, Z, levels=[-0.5, 0.5, 1.5],
                 colors=["#F4C7C3", "#CFE3F5"])
    axB.contour(100 * survivals, pressures, Z, levels=[0.5], colors="k", linewidths=1.5)
    axB.set_xlabel("Surviving elastin  [%]")
    axB.set_ylabel(r"Pressure factor  $\gamma$")
    axB.invert_xaxis()
    axB.text(50, 1.4, "ADAPTS", color="#1f5fa8", fontsize=12, ha="center")
    axB.text(12, 2.6, "ANEURYSM", color="#a83232", fontsize=12, ha="center")

    fig.tight_layout()
    print("wrote", save_pdf(fig, FIG))


if __name__ == "__main__":
    main()

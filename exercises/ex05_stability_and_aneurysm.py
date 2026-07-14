"""
EXERCISE 5 — Capstone: what makes a tissue stable?
==================================================

Read docs/07_stability.md first.

Goal: build the stable/unstable map yourself, then discover what pushes a tissue
back toward stability: a stronger mechano-response, stiffer collagen, or a higher
deposition prestretch.  Watch the "aneurysm" region shrink.

HOW TO RUN
    uv run python exercises/ex05_stability_and_aneurysm.py

Or, without editing any Python, run the same exercise from its YAML input file:
    uv run python run.py configs/ex05_stability.yaml
    uv run python run.py configs/ex05_stability.yaml --set model.constituents.collagen.gain=3.0
"""
from __future__ import annotations

import numpy as np

from gr import Insult, Model, artery
from gr.plotting import plt
from gr.stability import adapts

# =============================================================================
# YOUR TURN — change ONE property and see how the stability map moves.
# =============================================================================
# Baseline is the default tissue.  Try each of these (one at a time):
#   * raise the gain:            GAIN = 3.0
#   * stiffen collagen:          COLLAGEN_C1 = 600.0
#   * raise deposition stretch:  COLLAGEN_G = 1.15
GAIN = 1.0
COLLAGEN_C1 = 250.0
COLLAGEN_G = 1.08
# =============================================================================


def build_model() -> Model:
    from gr.mechanics import FungFiber
    return (Model()
            .with_constituent("collagen", gain=GAIN, G=COLLAGEN_G,
                              law=FungFiber(c1=COLLAGEN_C1, c2=8.0))
            .with_constituent("smc", gain=GAIN))


def main() -> None:
    art = artery(build_model())

    survivals = np.linspace(0.6, 0.02, 40)
    pressures = np.linspace(1.0, 3.0, 40)
    Z = np.array([[adapts(art, Insult(pressure_factor=float(p),
                                      elastin_surviving=float(s)))
                   for s in survivals] for p in pressures])

    frac_adapt = Z.mean()
    print(f"gain={GAIN}, collagen c1={COLLAGEN_C1}, G={COLLAGEN_G}")
    print(f"  fraction of the (elastin x pressure) map that ADAPTS: {frac_adapt:.2f}")
    print("  (bigger = more stable tissue)")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.contourf(100 * survivals, pressures, Z, levels=[-0.5, 0.5, 1.5],
                colors=["#F4C7C3", "#CFE3F5"])
    ax.contour(100 * survivals, pressures, Z, levels=[0.5], colors="k")
    ax.set(xlabel="surviving elastin [%]", ylabel=r"pressure factor $\gamma$",
           title="Stable (blue) vs unstable (red)")
    ax.invert_xaxis()
    ax.text(48, 1.4, "ADAPTS", color="#1f5fa8", ha="center")
    ax.text(12, 2.6, "ANEURYSM", color="#a83232", ha="center")
    fig.tight_layout()

    # QUESTIONS:
    #   * Which single change enlarges the blue (stable) region the most?
    #   * Elastin cannot be regrown in adults. What does that imply clinically
    #     about aneurysm, given what stabilises the tissue here?
    plt.show()


if __name__ == "__main__":
    main()

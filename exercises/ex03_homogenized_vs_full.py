"""
EXERCISE 3 — Homogenized vs. full constrained mixture
=====================================================

Read docs/05_homogenized_cmm.md first.

Goal: convince yourself that the homogenized model (two ODEs per constituent)
reproduces the full model (history integrals) — and runs much faster.

HOW TO RUN
    uv run python exercises/ex03_homogenized_vs_full.py

Or, without editing any Python, run the same comparison from its YAML input file:
    uv run python run.py configs/ex03_homogenized_vs_full.yaml
"""
from __future__ import annotations

import time

from gr import Insult, Model, artery, constrained_mixture, homogenized_cmm
from gr.plotting import STYLE, plt

# =============================================================================
# YOUR TURN
# =============================================================================
# Pick a scenario to compare the two models on.
INSULT = Insult(pressure_factor=1.5, t_on=1.0, ramp=1.0)          # hypertension
# INSULT = Insult(elastin_surviving=0.3, t_on=1.0, ramp=10.0)     # aneurysm

T_END = 2000.0
# =============================================================================


def main() -> None:
    art = artery(Model())

    t0 = time.time()
    full = constrained_mixture.simulate(art, INSULT, t_end=T_END, dt=1.0)
    t_full = time.time() - t0

    t0 = time.time()
    homog = homogenized_cmm.simulate(art, INSULT, t_end=T_END)
    t_homog = time.time() - t0

    # how far apart are the two trajectories?
    max_gap = max(abs(full.mass - homog.mass))
    print(f"full CMM took   {t_full:6.2f} s   (history integrals, O(N^2))")
    print(f"homogenized took {t_homog:6.2f} s   (two ODEs, O(N))")
    print(f"largest mass-ratio difference between them: {max_gap:.4f}")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for r in (full, homog):
        axes[0].plot(r.t, r.sigma_norm, label=r.theory, **STYLE[r.theory])
        axes[1].plot(r.t, r.mass, label=r.theory, **STYLE[r.theory])
    axes[0].axhline(1.0, color="gray", lw=1)
    axes[0].set(xlabel="time [day]", ylabel=r"$\bar\sigma/\bar\sigma_h$", title="stress")
    axes[1].set(xlabel="time [day]", ylabel=r"$M/M_0$", title="mass")
    axes[1].legend()
    fig.tight_layout()

    # QUESTIONS:
    #   * Is the difference between the two curves visible by eye?
    #   * By what factor is the homogenized model faster here?
    #   * Try a longer T_END or the aneurysm insult — does the agreement hold?
    plt.show()


if __name__ == "__main__":
    main()

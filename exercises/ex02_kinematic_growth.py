"""
EXERCISE 2 — Kinematic growth
=============================

Read docs/03_kinematic_growth.md first.

Goal: see that kinematic growth restores the *prescribed* homeostatic stress —
and that on the artery a strong enough insult can make it run away instead.

HOW TO RUN
    uv run python exercises/ex02_kinematic_growth.py

Or, without editing any Python, run the same exercise from its YAML input file
(and sweep a parameter in one line):
    uv run python run.py configs/ex02_kinematic_growth.yaml
    uv run python run.py configs/ex02_kinematic_growth.yaml --sweep simulate.k_g=0.02,0.05,0.2
"""
from __future__ import annotations

from gr import Insult, Model, artery, kinematic_growth
from gr.plotting import plt

# =============================================================================
# YOUR TURN
# =============================================================================
# (1) Growth-rate gain: how fast the tissue grows.  Try 0.02, 0.05, 0.2.
K_G = 0.05

# (2) The pressure step (hypertension).  Try 1.5, then push it up: 3.0, 5.0 ...
PRESSURE_FACTOR = 1.5
# =============================================================================


def main() -> None:
    model = Model()
    geom = artery(model)
    insult = Insult(pressure_factor=PRESSURE_FACTOR, t_on=1.0, ramp=1.0)

    r = kinematic_growth.simulate(geom, insult, k_g=K_G, t_end=1500)

    print(f"pressure x{PRESSURE_FACTOR},  k_g = {K_G}")
    print(f"  final stretch     lambda = {r.lam[-1]:.3f}")
    print(f"  final growth      theta  = {r.mass[-1]:.3f}")
    print(f"  final stress  sigma/sigma_h = {r.sigma_norm[-1]:.3f}")
    print(f"  RAN AWAY (unstable)?  {r.diverged}")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    axes[0].plot(r.t, r.sigma_norm, color="black")
    axes[0].axhline(1.0, color="gray", lw=1)
    axes[0].set(xlabel="time [day]", ylabel=r"$\bar\sigma/\bar\sigma_h$",
                title="stress vs set-point")
    axes[1].plot(r.t, r.mass, color="#4C72B0")
    axes[1].set(xlabel="time [day]", ylabel=r"growth $\theta$", title="growth")
    fig.suptitle(f"Kinematic growth — artery, P x{PRESSURE_FACTOR}")
    fig.tight_layout()

    # QUESTIONS:
    #   * Does the final stress ALWAYS return to 1 when it does not run away?
    #     (That is the "prescribed homeostasis" property.)
    #   * Roughly what PRESSURE_FACTOR tips the artery into runaway?
    plt.show()


if __name__ == "__main__":
    main()

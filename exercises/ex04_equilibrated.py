"""
EXERCISE 4 — The equilibrated model & the stability boundary
============================================================

Read docs/06_equilibrated_cmm.md first.

Goal: use the INSTANT equilibrated solve to (a) confirm it matches the transient
when an equilibrium exists, and (b) find the critical elastin loss beyond which
NO equilibrium exists — i.e. the tissue can no longer adapt.

HOW TO RUN
    uv run python exercises/ex04_equilibrated.py

Or, without editing any Python, run the same exercise from its YAML input file:
    uv run python run.py configs/ex04_equilibrated.yaml
"""
from __future__ import annotations

import numpy as np

from gr import Insult, Model, artery, equilibrated_cmm, homogenized_cmm
from gr.plotting import plt
from gr.stability import critical_elastin_loss

art = artery(Model())

# =============================================================================
# YOUR TURN — Part A: does the equilibrated solve match the transient?
# =============================================================================
# Pick a surviving-elastin fraction that DOES adapt (try 0.4, 0.3, 0.2).
ELASTIN_SURVIVING = 0.3
# =============================================================================


def part_A() -> None:
    insult = Insult(elastin_surviving=ELASTIN_SURVIVING, t_on=1.0, ramp=10.0)
    e = equilibrated_cmm.solve(art, insult)
    r = homogenized_cmm.simulate(art, insult, t_end=6000)
    print("PART A")
    print(f"  equilibrated exists? {e.exists}")
    if e.exists:
        print(f"  equilibrated lambda* = {e.lam:.3f}")
        print(f"  transient   lambda(t_end) = {r.lam[-1]:.3f}   (should be close)")


# =============================================================================
# YOUR TURN — Part B: find the stability boundary.
# =============================================================================
def part_B() -> None:
    # The equilibrated solve is instant, so we can scan many insults cheaply.
    survivals = np.linspace(0.6, 0.02, 60)
    lam = []
    for s in survivals:
        e = equilibrated_cmm.solve(art, Insult(elastin_surviving=float(s)))
        lam.append(e.lam if e.exists else np.nan)

    s_crit = critical_elastin_loss(art)
    print("\nPART B")
    print(f"  critical surviving elastin = {100*s_crit:.1f} %")
    print("  (above this the artery adapts; below it, unbounded growth)")

    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.plot(100 * survivals, lam, color="#C44E52", lw=2.5)
    ax.axvline(100 * s_crit, color="gray", ls="--", label=f"boundary ~ {100*s_crit:.0f}%")
    ax.set(xlabel="surviving elastin [%]", ylabel=r"evolved stretch $\lambda^*$",
           title="Equilibrated solve = instant stability test")
    ax.invert_xaxis()
    ax.legend()
    fig.tight_layout()

    # QUESTIONS:
    #   * The curve shoots up near the boundary. What is happening physically?
    #   * OPTIONAL: pick an ELASTIN_SURVIVING just BELOW s_crit and run a
    #     homogenized transient (t_end=8000). Does it run away?
    plt.show()


if __name__ == "__main__":
    part_A()
    part_B()

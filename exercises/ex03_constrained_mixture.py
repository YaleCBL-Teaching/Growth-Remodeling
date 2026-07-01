"""
EXERCISE 3 — The full constrained mixture model
===============================================

Read docs/04_constrained_mixture.md first.

Goal: watch turnover in action.  Collagen and smooth muscle are produced and
removed; elastin is not.  See how the turnover time and the mechano-sensitivity
gain control how fast (and whether) the wall adapts.

HOW TO RUN
    uv run python exercises/ex03_constrained_mixture.py
"""
from __future__ import annotations

from gr import Insult, Model, artery, constrained_mixture
from gr.plotting import plt

# =============================================================================
# YOUR TURN
# =============================================================================
# (1) Turnover time of collagen & muscle, in DAYS.  1/k_d is the mean lifetime.
#     Try 10 (fast), 20, 70 (aorta).  Faster turnover -> faster adaptation.
TURNOVER_DAYS = 20.0

# (2) Mechano-sensitivity gain K_sigma.  Try 0.3, 1.0, 3.0.
GAIN = 1.0

# (3) The insult.  Start with hypertension; then try the aneurysm line instead.
INSULT = Insult(pressure_factor=1.5, t_on=1.0, ramp=1.0)          # hypertension
# INSULT = Insult(elastin_surviving=0.3, t_on=1.0, ramp=10.0)     # aneurysm
# =============================================================================


def main() -> None:
    k_d = 1.0 / TURNOVER_DAYS
    model = (Model()
             .with_constituent("collagen", k_d=k_d, gain=GAIN)
             .with_constituent("smc", k_d=k_d, gain=GAIN))
    art = artery(model)

    r = constrained_mixture.simulate(art, INSULT, t_end=3000, dt=2.0)
    print(f"turnover = {TURNOVER_DAYS} d,  gain = {GAIN}")
    print(f"  final mass ratio     = {r.mass[-1]:.3f}")
    print(f"  final stress/sigma_h = {r.sigma_norm[-1]:.3f}")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for name, m in r.masses.items():
        axes[0].plot(r.t, m, label=name)
    axes[0].set(xlabel="time [day]", ylabel=r"constituent mass $M^k/M_0$",
                title="who grows?")
    axes[0].legend()
    axes[1].plot(r.t, r.sigma_norm, color="black")
    axes[1].axhline(1.0, color="gray", lw=1)
    axes[1].set(xlabel="time [day]", ylabel=r"$\bar\sigma/\bar\sigma_h$",
                title="stress restored by turnover")
    fig.tight_layout()

    # QUESTIONS:
    #   * With faster turnover, does the FINAL state change, or only the SPEED?
    #   * Switch to the aneurysm insult: which constituent takes over the load
    #     that the lost elastin used to carry?
    plt.show()


if __name__ == "__main__":
    main()

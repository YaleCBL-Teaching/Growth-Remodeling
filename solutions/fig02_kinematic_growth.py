"""
TEACHER solution / figure for Step 2 (kinematic growth).

docs/figures/fig02_kinematic_growth.pdf: kinematic growth adapting to a step
increase in pressure (hypertension), on the bar and on the artery.  Both restore
the *prescribed* homeostatic stress -- that is the defining feature (and the
limitation) of kinematic growth.

Run:  uv run python solutions/fig02_kinematic_growth.py
"""
from __future__ import annotations

from gr import HYPERTENSION, artery, bar, kinematic_growth
from gr.plotting import NEUTRAL, plt, save_pdf

from _scenarios import SEMINAR_MODEL

FIG = "docs/figures/fig02_kinematic_growth.pdf"


def main() -> None:
    model = SEMINAR_MODEL
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))

    # single theory (kinematic growth) on two geometries: neutral blue for the
    # artery (the case the videos show), slate for the bar; linestyle separates them.
    for geom, ls, color in [(bar(model), "--", "#7F7F7F"), (artery(model), "-", NEUTRAL)]:
        r = kinematic_growth.simulate(geom, HYPERTENSION, t_end=1000)
        axes[0].plot(r.t, r.sigma_norm, ls, color=color, label=geom.name)
        axes[1].plot(r.t, r.mass, ls, color=color, label=geom.name)
        axes[2].plot(r.t, r.lam, ls, color=color, label=geom.name)

    axes[0].axhline(1.0, color="gray", lw=1, alpha=0.6)
    axes[0].set_ylabel(r"Wall stress  $\bar\sigma/\bar\sigma_h$")
    axes[1].set_ylabel(r"Growth (mass ratio)  $\theta$")
    axes[2].set_ylabel(r"Stretch  $\lambda$")
    for ax in axes:
        ax.set_xlabel("Time  [day]")
        ax.legend()

    fig.suptitle("Kinematic growth under hypertension (P: 1.0 -> 1.5x)", y=1.03, fontsize=14)
    fig.tight_layout()
    print("wrote", save_pdf(fig, FIG))


if __name__ == "__main__":
    main()

"""
TEACHER solution / figure for Step 3 (full constrained mixture).

docs/figures/fig03_constrained_mixture.pdf: the turnover story, as the static
twin of ``video03_constrained_mixture``.  Under hypertension the full CMM grows
collagen and smooth muscle (which turn over) while elastin (which does not) is
merely diluted -- so collagen and muscle **remodel their stress back** to their
own homeostatic set-point while elastin's stress stays elevated, and the wall
thickens at nearly constant radius.  This is the mechanism the
homogenized/equilibrated theories approximate.

Run:  uv run python solutions/fig03_constrained_mixture.py
"""
from __future__ import annotations

from gr import HYPERTENSION, artery, constrained_mixture
from gr.plotting import CONSTITUENT_STYLE, NEUTRAL, constituent_order, plt, save_pdf

from _scenarios import SEMINAR_MODEL

FIG = "docs/figures/fig03_constrained_mixture.pdf"


def main() -> None:
    art = artery(SEMINAR_MODEL)
    r = constrained_mixture.simulate(art, HYPERTENSION, t_end=1200, dt=2.0)
    R0, H0 = SEMINAR_MODEL.R, SEMINAR_MODEL.H

    # Same panels (and palette) as the video: per-constituent stress & mass, then
    # the geometry as ratios to baseline.  Collagen is dashed and drawn last so it
    # never hides behind smooth muscle.
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    (axS, axM), (axR, axH) = axes

    # (a) per-constituent stress: collagen & smc remodel back to sigma_h^k;
    #     elastin cannot, so its stress stays elevated.
    for name in constituent_order(r.stresses):
        axS.plot(r.t, r.stresses[name], label=name, **CONSTITUENT_STYLE.get(name, {}))
    axS.axhline(1.0, color="gray", lw=1, ls=":", alpha=0.8)
    axS.set_ylabel(r"Constituent stress  $\sigma^k/\sigma_h^k$")
    axS.legend()

    # (b) per-constituent mass: collagen & smc grow; elastin is diluted.
    for name in constituent_order(r.masses):
        axM.plot(r.t, r.masses[name], label=name, **CONSTITUENT_STYLE.get(name, {}))
    axM.set_ylabel(r"Constituent mass  $M^k/M_0$")

    # (c) & (d) geometry as ratios to baseline -- neutral colour (single theory).
    axR.plot(r.t, r.radius / R0, color=NEUTRAL)
    axR.axhline(1.0, color="gray", lw=1, ls=":", alpha=0.8)
    axR.set_ylabel(r"Radius ratio  $a/a_0$")

    axH.plot(r.t, r.thickness / H0, color=NEUTRAL)
    axH.axhline(1.0, color="gray", lw=1, ls=":", alpha=0.8)
    axH.set_ylabel(r"Thickness ratio  $h/h_0$")

    for ax in axes.flat:
        ax.set_xlabel("Time  [day]")

    fig.suptitle("Full constrained-mixture model: adaptation to hypertension (artery)",
                 fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    print("wrote", save_pdf(fig, FIG))


if __name__ == "__main__":
    main()

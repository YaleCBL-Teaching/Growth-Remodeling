"""
TEACHER solution / figure for Step 3 (full constrained mixture).

docs/figures/fig03_constrained_mixture.pdf: the turnover story.  Under
hypertension the full CMM grows collagen and smooth muscle (which turn over)
while elastin (which does not) is merely diluted -- and the tissue stress returns
to homeostatic.  This is the mechanism the homogenized/equilibrated theories
approximate.

Run:  uv run python solutions/fig03_constrained_mixture.py
"""
from __future__ import annotations

from gr import HYPERTENSION, artery, constrained_mixture
from gr.plotting import plt, save_pdf

from _scenarios import SEMINAR_MODEL

FIG = "docs/figures/fig03_constrained_mixture.pdf"


def main() -> None:
    art = artery(SEMINAR_MODEL)
    r = constrained_mixture.simulate(art, HYPERTENSION, t_end=1200, dt=2.0)

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))

    # (a) per-constituent masses
    for name, m in r.masses.items():
        axes[0].plot(r.t, m, label=name)
    axes[0].set_ylabel(r"constituent mass  $M^k/M_0$")
    axes[0].set_title("(a) collagen & SMC grow; elastin does not")
    axes[0].legend()

    # (b) tissue stress back to homeostatic
    axes[1].plot(r.t, r.sigma_norm, color="black")
    axes[1].axhline(1.0, color="gray", lw=1, alpha=0.6)
    axes[1].set_ylabel(r"tissue stress  $\bar\sigma/\bar\sigma_h$")
    axes[1].set_title("(b) stress restored by turnover")

    # (c) geometry
    axes[2].plot(r.t, r.radius, label="inner radius $r$")
    axes[2].plot(r.t, r.thickness, label="thickness $h$")
    axes[2].set_ylabel("length  [mm]")
    axes[2].set_title("(c) wall thickens, radius ~ constant")
    axes[2].legend()

    for ax in axes:
        ax.set_xlabel("time  [day]")

    fig.suptitle("Full constrained-mixture model: adaptation to hypertension (artery)",
                 y=1.03, fontsize=14)
    fig.tight_layout()
    print("wrote", save_pdf(fig, FIG))


if __name__ == "__main__":
    main()

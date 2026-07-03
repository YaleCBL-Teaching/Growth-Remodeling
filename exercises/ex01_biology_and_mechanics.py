"""
EXERCISE 1 — Biology & finite-strain mechanics
==============================================

Read docs/01_biology.md and docs/02_finite_strain.md first.

Goal: get a feel for the constituent behaviour in **reference-configuration**
measures — the 2nd Piola-Kirchhoff stress S plotted against the Green-Lagrange
strain E — and for the deposition stretch G at which cells lay down new material.
(These are the measures the whole package is built on; the Cauchy "true" stress
is a push-forward of S, shown faintly for intuition.)

HOW TO RUN
    uv run python exercises/ex01_biology_and_mechanics.py

You only need to edit the small "YOUR TURN" block.  Everything else just plots.
"""
from __future__ import annotations

import numpy as np

from gr import Model
from gr.mechanics import FungFiber, NeoHookean, strain_gl
from gr.plotting import plt

# =============================================================================
# YOUR TURN — change these and re-run.  Suggested experiments below.
# =============================================================================
# (1) Collagen stiffening.  c2 controls how sharply collagen stiffens.
#     Try c2 = 2, 8, 20.  How does the S(E) curve change?
COLLAGEN_C1 = 250.0     # low-strain stiffness [kPa]
COLLAGEN_C2 = 8.0       # stiffening exponent [-]   <-- try 2, 8, 20

# (2) Elastin stiffness.  Try c_e = 30, 90, 200 [kPa].
ELASTIN_C = 90.0

# (3) Deposition stretch of collagen.  Try 1.02, 1.08, 1.20.
#     Watch how the marked homeostatic set-point (E(G), S(G)) moves.
COLLAGEN_G = 1.08
# =============================================================================


def main() -> None:
    elastin = NeoHookean(c=ELASTIN_C)
    collagen = FungFiber(c1=COLLAGEN_C1, c2=COLLAGEN_C2)

    lam = np.linspace(1.0, 1.4, 300)             # physiological window
    E = strain_gl(lam)                      # Green-Lagrange strain (reference)

    fig, ax = plt.subplots(figsize=(7, 5))
    for law, name in [(elastin, "elastin (neo-Hookean)"), (collagen, "collagen (Fung)")]:
        S = np.array([law.stress_pk2(x) for x in lam])   # 2nd PK stress (reference)
        line, = ax.plot(E, S, label=name)
        # faint Cauchy push-forward for intuition
        sig = np.array([law.stress_cauchy(x) for x in lam])
        ax.plot(E, sig, color=line.get_color(), lw=1, ls=":", alpha=0.5)

    # mark collagen's homeostatic set-point at the deposition stretch G
    E_h = strain_gl(COLLAGEN_G)
    S_h = collagen.stress_pk2(COLLAGEN_G)
    ax.plot([E_h], [S_h], "ko")
    ax.annotate(f"deposition stretch G={COLLAGEN_G}\n"
                f"E={E_h:.3f},  S={S_h:.0f} kPa",
                (E_h, S_h), xytext=(15, -30), textcoords="offset points",
                arrowprops=dict(arrowstyle="->"))

    ax.set_ylim(0, 200)                          # Fung stress runs off-scale at high E
    ax.set_xlabel(r"Green-Lagrange strain  $E_e = \frac{1}{2}(\lambda_e^2-1)$")
    ax.set_ylabel(r"2nd Piola-Kirchhoff stress  $S$  [kPa]")
    ax.set_title("Exercise 1: reference-config constituent laws  (dotted = Cauchy $\\sigma$)")
    ax.legend()
    fig.tight_layout()

    print(f"With G={COLLAGEN_G}: collagen set-point  E={E_h:.3f},  S={S_h:.1f} kPa,"
          f"  (Cauchy sigma={collagen.stress_cauchy(COLLAGEN_G):.1f} kPa)")
    print("Default mixture homeostatic Cauchy stress:",
          f"{Model().sigma_bar_h:.1f} kPa")

    # QUESTIONS to think about:
    #   * Why is collagen almost flat near E=0 but steep by E~0.4?
    #   * S is referential; the dotted Cauchy curve is its push-forward sigma =
    #     lambda_e^2 S.  Where do they differ most, and why?
    #   * If cells deposit collagen at a HIGHER prestretch G, does the tissue
    #     carry more or less homeostatic stress?
    plt.show()


if __name__ == "__main__":
    main()

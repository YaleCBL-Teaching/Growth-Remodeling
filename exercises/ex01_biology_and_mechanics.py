"""
EXERCISE 1 — Biology & finite-strain mechanics
==============================================

Read docs/01_biology.md and docs/02_finite_strain.md first.

Goal: get a feel for the three constituent stress-stretch laws and the all-
important deposition stretch G^k.  You will see why elastin is "soft" and
collagen "stiffens", and how the homeostatic stress sigma_h = sigma(G) is set.

HOW TO RUN
    uv run python exercises/ex01_biology_and_mechanics.py

You only need to edit the small "YOUR TURN" block.  Everything else just plots.
"""
from __future__ import annotations

import numpy as np

from gr import Model
from gr.mechanics import FungFiber, NeoHookean
from gr.plotting import plt

# =============================================================================
# YOUR TURN — change these and re-run.  Suggested experiments below.
# =============================================================================
# (1) Collagen stiffening.  c2 controls how sharply collagen stiffens.
#     Try c2 = 2, 8, 20.  How does the curve change?
COLLAGEN_C1 = 250.0     # low-strain stiffness [kPa]
COLLAGEN_C2 = 8.0       # stiffening exponent [-]   <-- try 2, 8, 20

# (2) Elastin stiffness.  Try c_e = 30, 90, 200 [kPa].
ELASTIN_C = 90.0

# (3) Deposition stretch of collagen.  Try 1.02, 1.08, 1.20.
#     Watch how the marked homeostatic stress sigma_h = sigma(G) moves.
COLLAGEN_G = 1.08
# =============================================================================


def main() -> None:
    elastin = NeoHookean(c=ELASTIN_C)
    collagen = FungFiber(c1=COLLAGEN_C1, c2=COLLAGEN_C2)

    lam = np.linspace(1.0, 1.6, 300)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(lam, [elastin.stress(x) for x in lam], label="elastin (neo-Hookean)")
    ax.plot(lam, [collagen.stress(x) for x in lam], label="collagen (Fung)")

    # mark collagen's homeostatic set-point sigma_h = sigma(G)
    sig_h = collagen.stress(COLLAGEN_G)
    ax.plot([COLLAGEN_G], [sig_h], "ko")
    ax.annotate(f"deposition stretch G={COLLAGEN_G}\n"
                f"=> homeostatic stress sigma_h={sig_h:.0f} kPa",
                (COLLAGEN_G, sig_h), xytext=(15, -30),
                textcoords="offset points",
                arrowprops=dict(arrowstyle="->"))

    ax.set_xlabel(r"elastic stretch $\lambda_e$")
    ax.set_ylabel(r"Cauchy stress $\sigma$ [kPa]")
    ax.set_title("Exercise 1: constituent laws & the deposition set-point")
    ax.legend()
    fig.tight_layout()

    # A little printout so you can compare numbers as you change parameters.
    print(f"With G={COLLAGEN_G}: collagen homeostatic stress sigma_h = {sig_h:.1f} kPa")
    print("Default mixture homeostatic stress (all constituents):",
          f"{Model().sigma_bar_h:.1f} kPa")

    # QUESTIONS to think about:
    #   * Why is collagen almost flat near lambda=1 but steep by lambda=1.4?
    #   * If cells deposit collagen at a HIGHER prestretch G, does the tissue
    #     carry more or less homeostatic stress?
    plt.show()


if __name__ == "__main__":
    main()

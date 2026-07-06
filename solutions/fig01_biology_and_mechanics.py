"""
TEACHER solution / figure generator for Step 1 (biology & finite-strain mechanics).

Produces docs/figures/fig01_constitutive.pdf:
  (a) the constituent laws in REFERENCE-configuration measures -- 2nd
      Piola-Kirchhoff stress S vs Green-Lagrange strain E -- with the deposition
      set-points (E(G^k), S(G^k)) marked (dotted = the Cauchy push-forward);
  (b) the artery's Laplace "required stress" feedback -- the quadratic exponent
      (lambda^2) that lets growth run away once too much elastin is lost.
      This is the *spatial* (Cauchy) balance, where a true stress genuinely enters.

Run:  uv run python solutions/fig01_biology_and_mechanics.py
"""
from __future__ import annotations

import numpy as np

from gr import Model, artery
from gr.mechanics import strain_gl
from gr.plotting import plt, save_pdf

FIG = "docs/figures/fig01_constitutive.pdf"


def main() -> None:
    model = Model()

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11, 4.4))

    # (a) reference-config constituent laws: 2nd PK S vs Green-Lagrange E -------
    # Focus on the physiological window: the Fung stress rises exponentially and
    # is off-scale well before E ~ 0.5.
    lam = np.linspace(1.0, 1.42, 200)
    E = strain_gl(lam)
    for c in model.constituents:
        S = np.array([c.law.stress_pk2(x) for x in lam])
        line, = axA.plot(E, S, label=f"{c.name}")
        # mark the deposition set-point (E(G^k), S(G^k))
        E_G, S_G = strain_gl(c.G), c.law.stress_pk2(c.G)
        axA.plot([E_G], [S_G], "o", color=line.get_color())
        axA.annotate(f"$G_{{{c.name[0]}}}={c.G}$", (E_G, S_G),
                     textcoords="offset points", xytext=(6, -11), fontsize=9,
                     color=line.get_color())
    axA.set_ylim(0, 170)
    axA.set_xlabel(r"Green-Lagrange strain  $E_e = \frac{1}{2}(\lambda_e^2-1)$")
    axA.set_ylabel(r"2nd Piola-Kirchhoff stress  $S^k$  [kPa]")
    axA.legend()

    # (b) required-stress feedback: the artery's Laplace exponent (lambda^2) ----
    lam = np.linspace(0.8, 1.6, 200)
    geom = artery(model)
    req = np.array([geom.required_stress(x, mass_ratio=1.0, load_factor=1.0)
                    for x in lam])
    axB.plot(lam, req / model.sigma_bar_h, color="#C44E52",
             label=r"artery  ($\lambda^2$, Laplace)")
    axB.axhline(1.0, color="gray", lw=1, alpha=0.6)
    axB.axvline(1.0, color="gray", lw=1, alpha=0.6)
    axB.set_xlabel(r"Stretch  $\lambda$")
    axB.set_ylabel(r"Required stress  $\sigma_{\rm req}/\bar\sigma_h$")
    axB.annotate("dilating raises the\nwall stress quadratically",
                 (1.3, 1.7), fontsize=9, ha="center",
                 color="#C44E52")
    axB.legend()

    fig.tight_layout()
    out = save_pdf(fig, FIG)
    print("wrote", out)


if __name__ == "__main__":
    main()

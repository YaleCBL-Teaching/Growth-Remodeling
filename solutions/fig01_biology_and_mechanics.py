"""
TEACHER solution / figure generator for Step 1 (biology & finite-strain mechanics).

Produces docs/figures/fig01_constitutive.pdf:
  (a) the three constituent stress-stretch laws, with their deposition stretches
      G^k and the homeostatic stresses sigma_h^k = sigma(G^k) marked;
  (b) the bar-vs-artery "required stress" feedback -- the single exponent (lambda
      vs lambda^2) that decides whether growth is self-limiting or can run away.

Run:  uv run python solutions/fig01_biology_and_mechanics.py
"""
from __future__ import annotations

import numpy as np

from gr import Model, artery, bar
from gr.plotting import plt, save_pdf

FIG = "docs/figures/fig01_constitutive.pdf"


def main() -> None:
    model = Model()

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11, 4.4))

    # (a) constituent stress-stretch laws --------------------------------------
    lam = np.linspace(1.0, 1.6, 200)
    for c in model.constituents:
        sig = np.array([c.law.stress(x) for x in lam])
        line, = axA.plot(lam, sig, label=f"{c.name}")
        # mark deposition stretch G^k and homeostatic stress sigma_h^k
        axA.plot([c.G], [c.sigma_h], "o", color=line.get_color())
        axA.annotate(f"$G_{{{c.name[0]}}}={c.G}$", (c.G, c.sigma_h),
                     textcoords="offset points", xytext=(6, -12), fontsize=9,
                     color=line.get_color())
    axA.set_xlabel(r"elastic stretch  $\lambda_e$")
    axA.set_ylabel(r"constituent Cauchy stress  $\sigma^k$  [kPa]")
    axA.set_title("(a) constituent laws & deposition set-points")
    axA.legend()

    # (b) required-stress feedback: bar (exponent 1) vs artery (exponent 2) -----
    lam = np.linspace(0.8, 1.6, 200)
    for geom, name in [(bar(model), "bar  ($\\lambda^1$)"),
                       (artery(model), "artery  ($\\lambda^2$, Laplace)")]:
        req = np.array([geom.required_stress(x, mass_ratio=1.0, load_factor=1.0)
                        for x in lam])
        axB.plot(lam, req / model.sigma_bar_h, label=name)
    axB.axhline(1.0, color="gray", lw=1, alpha=0.6)
    axB.axvline(1.0, color="gray", lw=1, alpha=0.6)
    axB.set_xlabel(r"stretch  $\lambda$")
    axB.set_ylabel(r"required stress  $\sigma_{\rm req}/\bar\sigma_h$")
    axB.set_title("(b) why the artery can run away")
    axB.annotate("dilating raises\nwall stress faster\nin the artery",
                 (1.4, 1.96), fontsize=9, ha="center",
                 color="#C44E52")
    axB.legend()

    fig.tight_layout()
    out = save_pdf(fig, FIG)
    print("wrote", out)


if __name__ == "__main__":
    main()

"""Split fig01 into two standalone figures:
   fig01a_constituent_laws.pdf  -- the three constituent stress-stretch laws (0D viz)
   fig01b_required_stress.pdf   -- bar vs artery required-stress feedback (stability)
"""
from __future__ import annotations
import numpy as np
from gr import Model, artery, bar
from gr.plotting import plt, save_pdf

def main() -> None:
    model = Model()

    # (a) constituent laws -----------------------------------------------------
    figA, axA = plt.subplots(figsize=(6.4, 4.6))
    lam = np.linspace(1.0, 1.6, 200)
    for c in model.constituents:
        sig = np.array([c.law.stress(x) for x in lam])
        line, = axA.plot(lam, sig, label=f"{c.name}", lw=2)
        axA.plot([c.G], [c.sigma_h], "o", color=line.get_color())
        axA.annotate(f"$G_{{{c.name[0]}}}={c.G}$", (c.G, c.sigma_h),
                     textcoords="offset points", xytext=(6, -12), fontsize=10,
                     color=line.get_color())
    axA.set_xlabel(r"elastic stretch  $\lambda_e$")
    axA.set_ylabel(r"constituent Cauchy stress  $\sigma^k$  [kPa]")
    axA.set_ylim(0, 400)   # physiological range: keep all three laws + set-points readable
    axA.set_xlim(1.0, 1.5)
    axA.legend(loc="upper left")
    print("wrote", save_pdf(figA, "docs/figures/fig01a_constituent_laws.pdf"))

    # (b) required-stress feedback --------------------------------------------
    figB, axB = plt.subplots(figsize=(6.4, 4.6))
    lam = np.linspace(0.8, 1.6, 200)
    for geom, name in [(bar(model), "bar  ($\\lambda^1$)"),
                       (artery(model), "artery  ($\\lambda^2$, Laplace)")]:
        req = np.array([geom.required_stress(x, mass_ratio=1.0, load_factor=1.0)
                        for x in lam])
        axB.plot(lam, req / model.sigma_bar_h, label=name, lw=2)
    axB.axhline(1.0, color="gray", lw=1, alpha=0.6)
    axB.axvline(1.0, color="gray", lw=1, alpha=0.6)
    axB.set_xlabel(r"stretch  $\lambda$")
    axB.set_ylabel(r"required stress  $\sigma_{\rm req}/\bar\sigma_h$")
    axB.annotate("dilating raises\nwall stress faster\nin the artery",
                 (1.4, 1.96), fontsize=10, ha="center", color="#C44E52")
    axB.legend()
    print("wrote", save_pdf(figB, "docs/figures/fig01b_required_stress.pdf"))

if __name__ == "__main__":
    main()

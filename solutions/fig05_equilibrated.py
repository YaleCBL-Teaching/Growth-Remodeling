"""
TEACHER solution / figure for Step 6 (equilibrated CMM).

docs/figures/fig05_equilibrated.pdf:
  (a) the homogenized transient settling exactly onto the equilibrated end-state
      (they MATCH when an equilibrium exists);
  (b) the evolved stretch vs insult severity from the *instant* equilibrated
      solve -- with the point where the equilibrium ceases to exist marked (the
      onset of unbounded growth).

Run:  uv run python solutions/fig05_equilibrated.py
"""
from __future__ import annotations

import numpy as np

from gr import Insult, artery, homogenized_cmm
from gr import equilibrated_cmm as eq
from gr.plotting import STYLE, plt, save_pdf
from gr.stability import sweep_elastin_loss

from _scenarios import SEMINAR_MODEL

FIG = "docs/figures/fig05_equilibrated.pdf"


def main() -> None:
    art = artery(SEMINAR_MODEL)
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11.5, 4.6))

    # (a) transient converges to the equilibrated state --------------------
    for s, t_end in [(0.4, 2500.0), (0.3, 4000.0)]:
        insult = Insult(elastin_surviving=s, t_on=1.0, ramp=10.0)
        r = homogenized_cmm.simulate(art, insult, t_end=t_end)
        e = eq.solve(art, insult)
        line, = axA.plot(r.t, r.lam, **STYLE["homogenized CMM"])
        axA.plot(r.t, r.lam, color=line.get_color(), lw=2,
                 label=f"homogenized, elastin {int(s*100)}%")
        if e.exists:
            axA.axhline(e.lam, **STYLE["equilibrated CMM"], alpha=0.9)
            axA.annotate(f"equilibrated $\\lambda^*={e.lam:.3f}$",
                         (r.t[-1] * 0.55, e.lam), fontsize=9,
                         color=STYLE["equilibrated CMM"]["color"],
                         va="bottom")
    axA.set_xlabel("Time  [day]")
    axA.set_ylabel(r"Stretch  $\lambda$")
    axA.legend(loc="lower right")

    # (b) equilibrated stretch vs insult severity, with existence boundary ---
    s = np.linspace(0.6, 0.01, 120)
    sw = sweep_elastin_loss(art, s)
    axB.plot(100 * sw["survival"], sw["lam"], color=STYLE["equilibrated CMM"]["color"], lw=2.5)
    # mark the boundary (last existing point going toward severe loss)
    exists = sw["exists"]
    if exists.any() and (~exists).any():
        # first index (scanning from mild to severe) where it stops existing
        idx = np.argmax(~exists)
        s_crit = sw["survival"][idx]
        axB.axvline(100 * s_crit, color="gray", ls="--")
        axB.annotate("no equilibrium\n(unbounded growth)",
                     (100 * s_crit - 2, np.nanmax(sw["lam"]) * 0.7),
                     ha="right", fontsize=10, color="#C44E52")
        axB.annotate("adapts", (100 * s_crit + 8, 1.1), fontsize=10, color="#4C72B0")
    axB.set_xlabel("Surviving elastin  [%]")
    axB.set_ylabel(r"Evolved stretch  $\lambda^*$")
    axB.invert_xaxis()  # severity increases to the right

    fig.tight_layout()
    print("wrote", save_pdf(fig, FIG))


if __name__ == "__main__":
    main()

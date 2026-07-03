"""
TEACHER solution / figure for Step 5 -- THE CENTREPIECE.

docs/figures/fig04_compare_all.pdf: all four theories on the same axes, for two
scenarios (hypertension, and a mild aneurysm = 30% elastin retained).  The
equilibrated end-state is drawn as a horizontal target line.

Take-aways to point at on the slide:
  * all four largely agree for the mild insults shown here;
  * the homogenized trajectory sits almost on top of the full CMM;
  * the equilibrated line is where the transients are heading;
  * kinematic growth under-responds to elastin loss (it cannot remodel
    individual constituents), so its curve separates in the aneurysm panel.

Run:  uv run python solutions/fig04_compare_all.py
"""
from __future__ import annotations

from gr import ANEURYSM, HYPERTENSION, artery
from gr.plotting import STYLE, plt, save_pdf

from _scenarios import SEMINAR_MODEL, run_all

FIG = "docs/figures/fig04_compare_all.pdf"


def _panel(ax, results, eq, getter, ylabel, eq_val=None):
    for r in results:
        ax.plot(r.t, getter(r), label=r.theory, **STYLE[r.theory])
    if eq is not None and eq.exists and eq_val is not None:
        ax.axhline(eq_val, label="equilibrated CMM", **STYLE["equilibrated CMM"])
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Time  [day]")


def main() -> None:
    art = artery(SEMINAR_MODEL)

    scenarios = [
        (r"Hypertension  ($P\times1.5$)", HYPERTENSION, 1000.0, 1.0),
        (r"Aneurysm  (elastin $\to$ 30%)", ANEURYSM, 6000.0, 2.0),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8.4))
    for row, (title, insult, t_end, cmm_dt) in enumerate(scenarios):
        results, eq = run_all(art, insult, t_end=t_end, cmm_dt=cmm_dt)
        _panel(axes[row][0], results, eq, lambda r: r.sigma_norm,
               r"Mixture stress  $\bar\sigma/\bar\sigma_h$", eq_val=eq.sigma_norm if eq.exists else None)
        axes[row][0].axhline(1.0, color="gray", lw=1, alpha=0.5)
        _panel(axes[row][1], results, eq, lambda r: r.mass,
               r"Mass ratio  $M/M_0$", eq_val=eq.mass if eq.exists else None)

    # single de-duplicated legend
    handles, labels = axes[0][0].get_legend_handles_labels()
    seen = {}
    for h, lb in zip(handles, labels):
        seen.setdefault(lb, h)
    fig.legend(seen.values(), seen.keys(), loc="upper center",
               ncol=4, bbox_to_anchor=(0.5, 1.04))
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    # scenario labels as bold headings centred above each row (no per-axes titles)
    for row, (title, *_rest) in enumerate(scenarios):
        top = max(axes[row][0].get_position().y1, axes[row][1].get_position().y1)
        fig.text(0.5, top + 0.012, title, ha="center", fontweight="bold", fontsize=13)
    print("wrote", save_pdf(fig, FIG))


if __name__ == "__main__":
    main()

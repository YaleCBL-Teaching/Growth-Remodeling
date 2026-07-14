"""
Schematic of the four homeostatic states of a mechanically loaded tissue.

Each panel is written as its OWN vector PDF into docs/figures/ so the slides can
lay them out two-per-frame:
  fig_homeostasis_a.pdf  mechanical homeostasis / tissue maintenance -- the
                         state jitters about a fixed set-point;
  fig_homeostasis_b.pdf  mechanical homeostasis -- a perturbation relaxes back
                         to the set-point;
  fig_homeostasis_c.pdf  adaptive homeostasis -- the perturbation relaxes to a
                         NEW (reset) set-point;
  fig_homeostasis_d.pdf  lost homeostasis -- the state fails to recover and runs
                         away past the set-point.

Redrawn after Humphrey & Schwartz, Annu. Rev. Biomed. Eng. (2021).

Run:  uv run python solutions/fig_homeostasis_states.py
"""
from __future__ import annotations

import numpy as np

from gr.plotting import plt, save_pdf

S0 = 0.30        # baseline / original set-point
TP = 0.30        # time of the perturbation
TAU = 0.16       # relaxation time constant
CURVE = dict(color="black", lw=2.4, solid_capstyle="round")


def _axes(ax, letter, title):
    """Arrow-style State/Time axes with no ticks, plus a bold panel letter."""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(1.6)
        ax.spines[side].set_color("black")
    # arrowheads at the open ends of the two visible spines
    ax.plot(1, 0, ">k", ms=8, transform=ax.get_yaxis_transform(), clip_on=False)
    ax.plot(0, 1, "^k", ms=8, transform=ax.get_xaxis_transform(), clip_on=False)
    ax.set_xlabel("Time", fontsize=13, fontweight="bold", loc="right")
    ax.set_ylabel("State", fontsize=13, fontweight="bold", loc="top")
    ax.text(-0.02, 1.18, letter, transform=ax.transAxes, fontsize=20,
            fontweight="bold", va="top", ha="right")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=8)


def _setpoint(ax, y, label, *, dy=-0.10, va="top"):
    ax.axhline(y, ls=(0, (5, 4)), color="black", lw=1.4)
    ax.text(0.98, y + dy, label, ha="right", va=va, fontsize=11)


def _pre_and_jump(ax, peak):
    """Flat baseline up to TP, then a vertical perturbation to `peak`."""
    ax.plot([0, TP], [S0, S0], **CURVE)
    ax.plot([TP, TP], [S0, peak], **CURVE)
    ax.text(TP + 0.02, peak + 0.06, "perturbation", fontsize=11, ha="left")


def _relax(peak, floor):
    t = np.linspace(TP, 1.0, 200)
    y = floor + (peak - floor) * np.exp(-(t - TP) / TAU)
    return t, y


def draw_a(ax):
    """A: mechanical homeostasis (tissue maintenance) -- jitter about set-point."""
    _axes(ax, "A", "Mechanical Homeostasis\n(Tissue Maintenance)")
    t = np.linspace(0, 1, 400)
    ax.plot(t, S0 + 0.05 * np.sin(2 * np.pi * 3.0 * t), **CURVE)
    _setpoint(ax, S0, "set-point")


def draw_b(ax):
    """B: mechanical homeostasis -- perturbation recovers to the set-point."""
    _axes(ax, "B", "Mechanical Homeostasis")
    _pre_and_jump(ax, peak=0.66)
    ax.plot(*_relax(0.66, S0), **CURVE)
    _setpoint(ax, S0, "set-point")


def draw_c(ax):
    """C: adaptive homeostasis -- perturbation relaxes to a reset set-point."""
    reset = 0.44
    _axes(ax, "C", "Adaptive Homeostasis")
    _pre_and_jump(ax, peak=0.80)
    ax.plot(*_relax(0.80, reset), **CURVE)
    _setpoint(ax, reset, "reset set-point")


def draw_d(ax):
    """D: lost homeostasis -- the state runs away past the set-point."""
    _axes(ax, "D", "Lost Homeostasis")
    _pre_and_jump(ax, peak=0.92)
    ax.plot(*_relax(0.92, 0.06), **CURVE)            # asymptote below set-point
    _setpoint(ax, S0, "set-point", dy=0.03, va="bottom")


PANELS = {"a": draw_a, "b": draw_b, "c": draw_c, "d": draw_d}


def main() -> None:
    for key, draw in PANELS.items():
        fig, ax = plt.subplots(figsize=(5.2, 3.6))
        draw(ax)
        fig.subplots_adjust(top=0.82, bottom=0.12, left=0.08, right=0.97)
        out = f"docs/figures/fig_homeostasis_{key}.pdf"
        print("wrote", save_pdf(fig, out))
        plt.close(fig)


if __name__ == "__main__":
    main()

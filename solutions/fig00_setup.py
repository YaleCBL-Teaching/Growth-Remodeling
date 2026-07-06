"""
TEACHER solution / figure for the setup (geometry & boundary conditions).

docs/figures/fig00_setup.pdf -- a schematic (not a simulation) of the mechanical
setting every model shares, its boundary conditions, and the two insults:
  (a) the thin-walled artery cross-section with the Laplace balance;
  (b) the two insults -- hypertension (pressure up) and aneurysm (elastin loss).

Annotated with the actual default parameter values from gr.Model().

Run:  uv run python solutions/fig00_setup.py
"""
from __future__ import annotations

import numpy as np
from matplotlib.patches import Annulus, Circle, FancyArrowPatch

from gr import Model
from gr.plotting import plt, save_pdf

FIG = "docs/figures/fig00_setup.pdf"

WALL = "#c9d6e5"      # wall fill
WALL_EDGE = "#2b3a4a"
LUMEN = "#eaf3fb"     # blood/lumen
PRES = "#2a6fb0"      # pressure arrows
STRESS = "#c0392b"    # stress arrows


def _arrow(ax, p0, p1, color, lw=1.6, style="-|>", mut=12):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=mut,
                                 color=color, lw=lw, zorder=6))


def draw_vessel(ax, center, r_in, wall, *, pressure=1.0, show_labels=True,
                ghost_r_in=None, degraded=False):
    """Draw an artery cross-section with pressure + hoop-stress arrows."""
    cx, cy = center
    r_out = r_in + wall
    # lumen (blood)
    ax.add_patch(Circle(center, r_in, facecolor=LUMEN, edgecolor="none", zorder=1))
    # wall (dashed + lighter if elastin degraded)
    ax.add_patch(Annulus(center, r_out, wall, facecolor=WALL, edgecolor=WALL_EDGE,
                         lw=1.6, ls="--" if degraded else "-",
                         alpha=0.6 if degraded else 1.0, zorder=2))
    # ghost of the original inner wall (for the insult panel)
    if ghost_r_in is not None:
        ax.add_patch(Circle(center, ghost_r_in, facecolor="none",
                            edgecolor="gray", ls=(0, (3, 3)), lw=1.2, zorder=3))
    # pressure arrows (radially outward from near centre to just inside the wall)
    n = 8
    for k in range(n):
        a = 2 * np.pi * k / n
        d = np.array([np.cos(a), np.sin(a)])
        _arrow(ax, center + 0.32 * r_in * d, center + 0.9 * r_in * d, PRES,
               lw=1.1 + 1.2 * (pressure - 1.0), mut=9 + 6 * (pressure - 1.0))
    if show_labels:
        # hoop stress: two tangential arrows at the top of the wall
        rm = r_in + wall / 2
        top = np.array([cx, cy + rm])
        _arrow(ax, top, top + [-0.42, 0], STRESS, style="-|>")
        _arrow(ax, top, top + [0.42, 0], STRESS, style="-|>")
        ax.text(cx, cy + rm + 0.16, r"$\sigma_\theta$", color=STRESS,
                ha="center", fontsize=13)
        # inner radius r
        a = np.deg2rad(215)
        d = np.array([np.cos(a), np.sin(a)])
        _arrow(ax, center, center + r_in * d, WALL_EDGE, style="-|>", lw=1.2, mut=9)
        ax.text(*(center + 0.55 * r_in * d + [-0.05, -0.12]), "$r$",
                ha="center", fontsize=12)
        # thickness h (double arrow across the wall on the right)
        a = np.deg2rad(35)
        d = np.array([np.cos(a), np.sin(a)])
        _arrow(ax, center + r_in * d, center + r_out * d, WALL_EDGE, style="<|-|>",
               lw=1.2, mut=8)
        ax.text(*(center + (r_out + 0.14) * d), "$h$", ha="center", fontsize=12)
        # pressure label
        ax.text(cx, cy - 0.02, "$P$", color=PRES, ha="center", va="center",
                fontsize=14, fontweight="bold")


def main() -> None:
    m = Model()
    fig = plt.figure(figsize=(10, 5.2))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 0.9], wspace=0.12)
    axB, axC = (fig.add_subplot(gs[0, i]) for i in range(2))
    for ax in (axB, axC):
        ax.set_aspect("equal")
        ax.axis("off")

    # ---- (a) thin-walled artery + Laplace -----------------------------------
    axB.set_xlim(-1.7, 1.7)
    axB.set_ylim(-1.75, 1.75)
    axB.set_title("(a) thin-walled artery (cross-section)", fontsize=13)
    draw_vessel(axB, (0, 0.15), r_in=0.85, wall=0.3, pressure=1.0)
    axB.text(0, -1.5,
             r"Laplace:  $\sigma_\theta = P\,r/h \;\propto\; \lambda^{2}$",
             ha="center", fontsize=12, color=STRESS)
    axB.text(1.35, -1.35, r"$\odot\,z,\ \lambda_z$", fontsize=11, ha="center")

    # ---- (b) the two insults ------------------------------------------------
    axC.set_xlim(-1.5, 1.5)
    axC.set_ylim(-2.7, 2.7)
    axC.set_title("(b) the two insults", fontsize=13)
    # hypertension: same radius, thicker wall, stronger pressure
    draw_vessel(axC, (0, 1.35), r_in=0.5, wall=0.34, pressure=1.6,
                show_labels=False)
    axC.text(0, 2.55, r"hypertension:  $P\!\uparrow$  $\Rightarrow$ wall thickens",
             ha="center", fontsize=10.5, color=PRES)
    # aneurysm: dilated lumen, thin degraded wall, ghost of original size
    draw_vessel(axC, (0, -1.25), r_in=0.78, wall=0.14, pressure=1.0,
                show_labels=False, degraded=True, ghost_r_in=0.5)
    axC.text(0, -2.5, "aneurysm:  elastin lost  $\\Rightarrow$ dilation",
             ha="center", fontsize=10.5, color=STRESS)

    fig.suptitle(
        f"Shared setting:  $R={m.R:.1f}$ mm,  $H={m.H*1e3:.0f}\\,\\mu$m,  "
        f"$P_h={m.P_h:.1f}$ kPa,  $\\bar\\sigma_h={m.sigma_bar_h:.0f}$ kPa",
        fontsize=12, y=1.02)
    print("wrote", save_pdf(fig, FIG))


if __name__ == "__main__":
    main()

r"""
Shared plotting helpers so every exercise and solution produces consistent,
presentation-ready figures.

Nothing here is theory-specific: it just takes :class:`~gr.history.Result`
objects (and optional :class:`~gr.equilibrated_cmm.Equilibrium` end states) and
lays them out.  Colours are fixed per theory so the same theory always looks the
same across every figure in the lecture.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from .equilibrated_cmm import Equilibrium
from .history import Result

# Two DISTINCT palettes so theories and constituents never share a colour.
# Theories (comparison plots):
STYLE = {
    "kinematic growth": dict(color="#6A3D9A", ls="-"),   # purple
    "full CMM": dict(color="#A6761D", ls="-"),           # brown/gold
    "homogenized CMM": dict(color="#E7298A", ls="--"),   # magenta
    "equilibrated CMM": dict(color="#C44E52", ls=":"),   # red (target)
}
# Constituents (per-constituent plots) -- collagen dashed so it never hides
# behind smooth muscle when they overlap:
CONSTITUENT_STYLE = {
    "elastin": dict(color="#4C72B0", ls="-"),            # blue
    "collagen": dict(color="#DD8452", ls="--"),          # orange, dashed
    "smc": dict(color="#55A868", ls="-"),                # green
}
# Draw order: solid lines first, dashed collagen LAST so it sits on top and its
# dashes stay visible wherever it overlaps smooth muscle / elastin.
CONSTITUENT_ORDER = ("elastin", "smc", "collagen")


def constituent_order(names) -> list:
    """Sort constituent names into the fixed draw order (unknown names last)."""
    n = len(CONSTITUENT_ORDER)
    return sorted(names, key=lambda x: CONSTITUENT_ORDER.index(x) if x in CONSTITUENT_ORDER else n)
# Neutral colour for a single theory's aggregate quantities (mass, radius, ...).
NEUTRAL = "#4C72B0"

# Nice defaults for slides (large fonts, clean spines).
plt.rcParams.update(
    {
        "figure.dpi": 120,
        "savefig.dpi": 200,
        "font.size": 12,
        "axes.titlesize": 13,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "lines.linewidth": 2.2,
        "legend.frameon": False,
    }
)


def _style(theory: str) -> dict:
    return STYLE.get(theory, dict(color="gray", ls="-"))


def _repo_root() -> Path:
    """Locate the repository root (the directory containing pyproject.toml).

    Anchoring output here makes ``save_pdf('docs/figures/...')`` land in the same
    place no matter which directory you launch the script from.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return here.parent


def save_pdf(fig, path: str | Path) -> Path:
    """Save a figure as a vector PDF (for slides) AND a PNG (for the markdown docs).

    A relative ``path`` is resolved against the repository root, so figures
    always land in ``<repo>/docs/figures/`` regardless of the working directory.
    The PDF is the slide-ready vector version; a same-named ``.png`` is written
    alongside so the markdown lecture notes can embed the figure inline.
    """
    path = Path(path)
    if not path.is_absolute():
        path = _repo_root() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    fig.savefig(path.with_suffix(".png"), bbox_inches="tight", dpi=150)
    return path


# Which Result field to plot, and how to label the y-axis.
_QUANTITIES = {
    "sigma_norm": (r"Wall stress  $\bar\sigma/\bar\sigma_h$", lambda r: r.sigma_norm),
    "mass": (r"Mass ratio  $M/M_0$", lambda r: r.mass),
    "lam": (r"Stretch  $\lambda$", lambda r: r.lam),
    "radius": ("Mid-wall radius / length  [mm]", lambda r: r.radius),
    "thickness": ("Wall thickness  [mm]", lambda r: r.thickness),
}


def compare(
    results: list[Result],
    quantities: tuple[str, ...] = ("sigma_norm", "mass", "radius"),
    equilibria: dict[str, Equilibrium] | None = None,
    title: str | None = None,
):
    """Overlay several theories on one row of time-history panels.

    Parameters
    ----------
    results : list of Result
        One per theory (all from the same scenario/geometry).
    quantities : which panels to draw (keys of ``_QUANTITIES``).
    equilibria : optional dict {label -> Equilibrium} drawn as target markers.
    """
    n = len(quantities)
    fig, axes = plt.subplots(1, n, figsize=(4.6 * n, 4.0))
    if n == 1:
        axes = [axes]

    for ax, q in zip(axes, quantities):
        ylabel, getter = _QUANTITIES[q]
        for r in results:
            ax.plot(r.t, getter(r), label=r.theory, **_style(r.theory))
        # homeostatic reference line for the normalised stress
        if q == "sigma_norm":
            ax.axhline(1.0, color="gray", lw=1, ls="-", alpha=0.5)
        # equilibrated end-state markers
        if equilibria:
            for eq in equilibria.values():
                if not eq.exists:
                    continue
                yval = {
                    "sigma_norm": eq.sigma_norm,
                    "mass": eq.mass,
                    "lam": eq.lam,
                    "radius": eq.radius,
                    "thickness": eq.thickness,
                }[q]
                ax.axhline(yval, **_style("equilibrated CMM"), alpha=0.9,
                           label="equilibrated CMM")
        ax.set_xlabel("Time  [day]")
        ax.set_ylabel(ylabel)

    # de-duplicate legend entries (equilibrium line may repeat)
    handles, labels = axes[0].get_legend_handles_labels()
    seen: dict[str, object] = {}
    for h, lb in zip(handles, labels):
        seen.setdefault(lb, h)
    axes[-1].legend(seen.values(), seen.keys(), loc="best")

    if title:
        fig.suptitle(title, fontsize=15, y=1.02)
    fig.tight_layout()
    return fig, axes

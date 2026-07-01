r"""
Stability helpers for the capstone (docs/07_stability.md).

The cleanest test of whether a tissue can adapt to a sustained insult is simply
whether a **mechanobiological equilibrium exists** — which the equilibrated model
answers instantly (``gr.equilibrated_cmm.solve``).  These helpers sweep that test
over a range of insults so you can draw the stable/unstable boundary without
waiting out the (ever slower!) transients near the boundary.
"""
from __future__ import annotations

import numpy as np

from . import equilibrated_cmm as eq
from .geometry import Geometry
from .parameters import Insult


def adapts(geom: Geometry, insult: Insult) -> bool:
    """True if a mechanobiological equilibrium exists for this sustained insult."""
    return eq.solve(geom, insult).exists


def sweep_elastin_loss(geom: Geometry, survivals: np.ndarray) -> dict:
    """Evolved stretch vs surviving-elastin fraction; NaN where no equilibrium.

    Returns a dict with arrays ``survival``, ``lam`` (evolved stretch, NaN if the
    tissue cannot adapt), and ``exists`` (bool mask).
    """
    lam = np.full_like(survivals, np.nan, dtype=float)
    exists = np.zeros_like(survivals, dtype=bool)
    for i, s in enumerate(survivals):
        e = eq.solve(geom, Insult(elastin_surviving=float(s)))
        exists[i] = e.exists
        if e.exists:
            lam[i] = e.lam
    return {"survival": survivals, "lam": lam, "exists": exists}


def critical_elastin_loss(geom: Geometry, lo: float = 0.0, hi: float = 1.0,
                          tol: float = 1e-3) -> float:
    """Bisect for the surviving-elastin fraction at the stability boundary.

    Above the returned value an equilibrium exists (the artery adapts); below it,
    none exists (unbounded dilatation).  Assumes ``adapts`` is monotone in s.
    """
    assert adapts(geom, Insult(elastin_surviving=hi)), "need an adapting upper bound"
    if adapts(geom, Insult(elastin_surviving=lo)):
        return lo
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if adapts(geom, Insult(elastin_surviving=mid)):
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)

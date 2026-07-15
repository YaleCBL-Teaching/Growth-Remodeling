r"""
Stability helpers for the capstone (docs/07_stability.md).

A necessary test of whether a tissue can adapt to a sustained insult is whether a
**mechanobiological equilibrium exists** -- which the equilibrated model answers
instantly (``gr.equilibrated_cmm.solve``).  These helpers sweep that test over a
range of insults so you can draw the existence boundary without waiting out the
(ever slower!) transients near it.

**Necessary, not sufficient.**  Existence depends only on the wall's load-bearing
capacity (elastin loss, constituent stiffness, deposition stretch) -- *not* on the
mechano-sensitivity ``gain``: at equilibrium production balances removal and the
gain cancels out.  Whether the transient actually *reaches* an equilibrium that
exists is a separate, gain-dependent question (mechanobiological *dynamic*
stability, Cyron & Humphrey 2014): if adaptation is too weak the artery can run
away even where a root exists.  So ``adapts`` here means "an equilibrium exists",
which is the existence boundary, not the full dynamic-stability boundary.  Explore
the gain-dependent part with the transient models (``gr.homogenized_cmm``) at a low
gain near the boundary; see docs/07_stability.md.
"""
from __future__ import annotations

import numpy as np

from . import equilibrated_cmm as eq
from .geometry import Geometry
from .parameters import Insult


def adapts(geom: Geometry, insult: Insult) -> bool:
    """True if a mechanobiological equilibrium *exists* for this sustained insult.

    This is the necessary (capacity) condition; the gain-dependent dynamic-stability
    check is separate -- see the module docstring.
    """
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

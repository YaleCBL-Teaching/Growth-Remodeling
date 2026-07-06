r"""
Theory 4 of 4 — EQUILIBRATED CONSTRAINED MIXTURE MODEL
(Latorre & Humphrey, 2018, "mechanobiologically equilibrated" CMM).

Why integrate a slow transient at all if you only care about the *final* adapted
state?  The equilibrated model sets every rate to zero and solves the resulting
**algebraic** system directly — one Newton solve instead of thousands of time
steps.

-------------------------------------------------------------------------------
The equilibrium conditions (docs/06_equilibrated_cmm.md)
-------------------------------------------------------------------------------
At mechanobiological equilibrium:

  (A) Mass production balances removal  =>  Upsilon = 1  =>  the tissue stress
      returns to homeostatic:                 sigma_bar* = sigma_bar_h
  (B) Remodeling has run its course      =>  every turnover constituent sits at
      its deposition stretch:                 lambda_e^k = G^k  =>  sigma^k = sigma_h^k
  (C) Mechanical (Laplace) equilibrium holds at the evolved geometry.

Elastin cannot remodel or be produced: its mass is just the surviving fraction s
and its stress follows the evolved stretch, sigma_e(G_e lambda*).  With the
turnover constituents growing in fixed proportion by a factor beta, conditions
(A)-(C) collapse to a SINGLE scalar equation for the evolved stretch lambda*
(full derivation in docs/06):

    phi_e0 * s
      + s * ( sigma_bar_h - sigma_e(G_e lambda*) ) / ( sigma_turn - sigma_h^e )
      - gamma * lambda*^n  =  0                                            (EQ)

where n = 2 is the Laplace exponent for the artery, gamma the load factor,
s the surviving elastin fraction, sigma_turn the mass-weighted homeostatic stress
of the turnover constituents, and sigma_h^e the homeostatic elastin stress.

-------------------------------------------------------------------------------
The key learning (docs/06, docs/07)
-------------------------------------------------------------------------------
Equation (EQ) may or may not have a physical root:

  * If a root exists, it coincides with the long-time limit of the full and
    homogenized transient models — **the equilibrated theory matches the
    transient theories**, for a tiny fraction of the cost.
  * If NO root exists, there is no adapted state to converge to: the transient
    models dilate without bound.  **The equilibrated theory returns "no
    equilibrium" precisely when the tissue is mechanobiologically unstable.**

This is why an equilibrium solver is also the cleanest stability test you can
run — see the exercise in docs/07_stability.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import brentq

from .geometry import Geometry
from .parameters import Insult


@dataclass
class Equilibrium:
    """Result of an equilibrated-CMM solve (an end state, not a trajectory)."""

    exists: bool
    setting: str
    sigma_h: float
    lam: float = float("nan")          # evolved global stretch lambda*
    mass: float = float("nan")         # evolved total mass ratio M/M_0
    beta: float = float("nan")         # turnover-mass growth factor
    radius: float = float("nan")       # evolved mid-wall radius / length [mm]
    thickness: float = float("nan")    # evolved wall thickness [mm]
    masses: dict[str, float] = field(default_factory=dict)
    stresses: dict[str, float] = field(default_factory=dict)  # per-constituent sigma^k/sigma_h^k

    @property
    def sigma_norm(self) -> float:
        """By construction the tissue stress is back to homeostatic when a root exists."""
        return 1.0 if self.exists else float("nan")


def solve(
    geom: Geometry,
    insult: Insult,
    bracket: tuple[float, float] = (0.2, 8.0),
) -> Equilibrium:
    """Solve the equilibrated CMM, Eq. (EQ).  Returns ``exists=False`` if none."""
    model = geom.model
    n = geom.stress_exponent
    gamma = insult.pressure_factor          # sustained load factor
    s = insult.elastin_surviving            # sustained surviving elastin fraction

    elastin = model.by_name("elastin")
    turnover = [c for c in model.constituents if c.k_d > 0.0]
    phi_e0 = elastin.phi0
    phi_turn0 = sum(c.phi0 for c in turnover)
    sigma_turn = sum(c.phi0 * c.sigma_h for c in turnover) / phi_turn0
    sigma_h_e = elastin.sigma_h
    denom = sigma_turn - sigma_h_e
    if abs(denom) < 1e-9:
        # Degenerate: turnover and elastin set-points coincide (guard for exotic params).
        return Equilibrium(exists=False, setting=geom.name, sigma_h=model.sigma_bar_h)

    def g(lam: float) -> float:
        return (
            phi_e0 * s
            + s * (model.sigma_bar_h - elastin.law.stress_cauchy(elastin.G * lam)) / denom
            - gamma * lam**n
        )

    # Equation (EQ) can have several roots; the physical one is the branch that
    # is continuously connected to the homeostatic state (lambda = 1 at no
    # insult), i.e. the root nearest lambda = 1.  Scan for all sign changes and
    # pick the closest to 1.  No sign change -> no equilibrium exists (the tissue
    # cannot adapt, and the transient theories run away).
    grid = np.linspace(bracket[0], bracket[1], 600)
    vals = np.array([g(x) for x in grid])
    roots = []
    for k in range(len(grid) - 1):
        if vals[k] == 0.0:
            roots.append(grid[k])
        elif vals[k] * vals[k + 1] < 0.0:
            roots.append(brentq(g, grid[k], grid[k + 1], xtol=1e-10, rtol=1e-12))
    if not roots:
        return Equilibrium(exists=False, setting=geom.name, sigma_h=model.sigma_bar_h)
    lam = min(roots, key=lambda x: abs(x - 1.0))

    # back out the turnover growth factor beta and the evolved masses
    beta = s * (model.sigma_bar_h - elastin.law.stress_cauchy(elastin.G * lam)) / denom / phi_turn0
    mass = gamma * lam**n                  # M/M_0 from Laplace at sigma_bar = sigma_bar_h
    masses = {"elastin": phi_e0 * s}
    for c in turnover:
        masses[c.name] = c.phi0 * beta
    # per-constituent stress at equilibrium: turnover back at sigma_h^k (=1);
    # elastin cannot remodel, so it carries sigma_e(G_e lambda*)/sigma_h^e
    stresses = {c.name: 1.0 for c in turnover}
    stresses["elastin"] = elastin.law.stress_cauchy(elastin.G * lam) / elastin.sigma_h

    return Equilibrium(
        exists=True,
        setting=geom.name,
        sigma_h=model.sigma_bar_h,
        lam=lam,
        mass=mass,
        beta=beta,
        radius=geom.radius(lam),
        thickness=geom.thickness(lam, mass),
        masses=masses,
        stresses=stresses,
    )

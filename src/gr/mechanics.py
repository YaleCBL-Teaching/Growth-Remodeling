r"""
Finite-strain constitutive mechanics — the *shared* material behaviour used by
**all four** G&R theories in this package.

Every theory in this repository (kinematic growth, full / homogenized /
equilibrated constrained mixture) plugs into the *same* constitutive laws
defined here.  That is deliberate: the theories must differ only in **how the
tissue evolves**, never in the underlying elasticity, so that any difference you
see in the exercises is caused by the growth-and-remodeling law and nothing
else.

-------------------------------------------------------------------------------
Notation (see docs/02_finite_strain.md for the full development)
-------------------------------------------------------------------------------
We work with a single scalar stretch per constituent, because both the 1D bar
and the thin-walled artery reduce the mechanics to one dominant direction:

    lambda_e   elastic stretch of a constituent = (current length)
                                                   / (its own natural length)

The Cauchy (true) stress carried by a constituent is a function sigma(lambda_e).
A constituent is **stress-free** at lambda_e = 1 and, in this package, is
**deposited** by the cells at a homeostatic pre-stretch lambda_e = G (the
deposition stretch, > 1 for fibers laid down under tension; see biology §1.3).

Two constitutive laws cover the arterial constituents:

  * Elastin  -> incompressible neo-Hookean fiber (soft, non-stiffening)
        sigma(l) = c * (l**2 - 1/l)                                       (M1)

  * Collagen / smooth muscle -> Fung-type exponential fiber (stiffening)
        psi(l)   = c1/(4 c2) * ( exp[c2 (l**2 - 1)**2] - 1 )             (M2)
        sigma(l) = c1 * l**2 * (l**2 - 1) * exp[c2 (l**2 - 1)**2]        (M3)

Each law also exposes its **material tangent** d(sigma)/d(lambda_e).  The tangent
is needed twice: (i) Newton solves for mechanical equilibrium, and (ii) the
linear-stability analysis in docs/07_stability.md, where the *sign* of the
stiffness sets whether growth is self-limiting or runs away.
"""
from __future__ import annotations

from dataclasses import dataclass


class MaterialLaw:
    """Base class: a 1D hyperelastic fiber law sigma(lambda_e)."""

    def stress(self, lam: float) -> float:
        """Cauchy (true) stress at elastic stretch ``lam``."""
        raise NotImplementedError

    def tangent(self, lam: float) -> float:
        """Material tangent d(sigma)/d(lam)."""
        raise NotImplementedError


@dataclass(frozen=True)
class NeoHookean(MaterialLaw):
    r"""
    Incompressible neo-Hookean fiber, Eq. (M1).

        sigma(l) = c (l^2 - 1/l),      d sigma/dl = c (2 l + 1/l^2)

    Soft and only mildly nonlinear — the right description for **elastin**, which
    behaves like a rubber and does *not* stiffen appreciably over the
    physiological range.

    Parameters
    ----------
    c : float
        Shear-modulus-like stiffness [kPa].
    """

    c: float  # [kPa]

    def stress(self, lam: float) -> float:
        return self.c * (lam**2 - 1.0 / lam)

    def tangent(self, lam: float) -> float:
        return self.c * (2.0 * lam + 1.0 / lam**2)


@dataclass(frozen=True)
class FungFiber(MaterialLaw):
    r"""
    Fung-type exponential fiber, Eqs. (M2)-(M3) — the standard model for the
    **collagen** and **smooth-muscle** fibers, which are crimped at rest and
    stiffen steeply once recruited.

        sigma(l) = c1 l^2 (l^2 - 1) exp[c2 (l^2 - 1)^2]

    The analytic tangent (derived in docs/02_finite_strain.md) is

        d sigma/dl = 2 c1 l exp[c2 E^2] * ( (2 l^2 - 1) + 2 c2 l^2 E^2 ),
        with E = l^2 - 1.

    Parameters
    ----------
    c1 : float
        Low-strain stiffness [kPa].
    c2 : float
        Dimensionless stiffening (exponential) parameter [-].
    """

    c1: float  # [kPa]
    c2: float  # [-]

    def stress(self, lam: float) -> float:
        E = lam**2 - 1.0
        return self.c1 * lam**2 * E * _exp(self.c2 * E**2)

    def tangent(self, lam: float) -> float:
        E = lam**2 - 1.0
        return 2.0 * self.c1 * lam * _exp(self.c2 * E**2) * (
            (2.0 * lam**2 - 1.0) + 2.0 * self.c2 * lam**2 * E**2
        )


def _exp(x):
    """np.exp with a guard so runaway aneurysm solves don't overflow.

    Works on both Python floats and NumPy arrays (the full constrained-mixture
    model sums the stress over many cohorts at once, ``gr.constrained_mixture``).
    """
    import numpy as np

    # Clip well below exp's overflow so that (polynomial factor) * exp() stays
    # finite even at the absurd stretches a runaway aneurysm solve probes.
    return np.exp(np.minimum(x, 300.0))

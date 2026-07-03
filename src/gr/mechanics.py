r"""
Finite-strain constitutive mechanics — the *shared* material behaviour used by
**all four** G&R theories in this package.

Every theory (kinematic growth, full / homogenized / equilibrated constrained
mixture) plugs into the *same* constitutive laws defined here, so any difference
you see in the exercises is caused by the growth-and-remodeling law and nothing
else.

-------------------------------------------------------------------------------
Everything is grounded in the REFERENCE configuration
-------------------------------------------------------------------------------
Following finite-strain theory (see docs/02_finite_strain.md), a constituent's
elastic response is written with **reference-configuration** strain and stress
measures — the ones referred to its own natural (stress-free) configuration:

    lambda_e   elastic stretch  (current length / natural length)
    E_e = 1/2 (lambda_e^2 - 1)        Green-Lagrange strain      (reference)     (M0)
    W(lambda_e)                       strain energy per unit reference volume
    S = dW/dE_e                       2nd Piola-Kirchhoff stress (reference)     (M1)

The two are work-conjugate (S : dE_e is the stress power per reference volume),
which is exactly what "grounded in the reference configuration" means.  From S we
obtain, when a *spatial* quantity is genuinely needed (e.g. the Laplace balance
of a pressurised artery), the **nominal (1st PK)** and **Cauchy (true)** stresses
by explicit push-forward — for a 1-D incompressible fiber (J = 1):

    P = lambda_e * S      1st Piola-Kirchhoff / nominal  (force per REFERENCE area) (M2)
    sigma = lambda_e^2 S  Cauchy / true                  (force per current area)   (M3)

A constituent is stress-free at lambda_e = 1 and is **deposited** by the cells at
a homeostatic pre-stretch lambda_e = G (the deposition stretch, > 1 for fibers
laid down under tension; see biology §1.3).

-------------------------------------------------------------------------------
The two constituent strain-energy functions (per unit reference volume)
-------------------------------------------------------------------------------
  * Elastin  -> incompressible neo-Hookean (soft, non-stiffening):
        W_e = (c/2) (I1 - 3),  I1 = lambda_e^2 + 2/lambda_e
        S_e = c (1 - lambda_e^{-3})                                            (NH)

  * Collagen / SMC -> Fung-type exponential fiber (stiffening), I4 = lambda_e^2:
        W   = c1/(4 c2) ( exp[c2 (I4 - 1)^2] - 1 )
        S   = c1 (lambda_e^2 - 1) exp[c2 (lambda_e^2 - 1)^2]                   (FUNG)

Both push forward (M3) to the same Cauchy stresses used before this refactor, so
the numerical results are unchanged — only the *formulation* is now referential.
"""
from __future__ import annotations

from dataclasses import dataclass


def green_lagrange(lam: float):
    r"""Elastic Green-Lagrange strain E_e = 1/2 (lambda_e^2 - 1), Eq. (M0).

    A purely kinematic, reference-configuration strain measure (same for every
    constituent); E_e = 0 in the natural configuration.
    """
    return 0.5 * (lam**2 - 1.0)


class MaterialLaw:
    """Base class: a 1-D hyperelastic fiber written in reference measures.

    Subclasses provide the strain energy ``energy`` and the 2nd Piola-Kirchhoff
    stress ``second_piola``; the nominal and Cauchy stresses are derived here by
    push-forward, Eqs. (M2)-(M3).
    """

    # --- reference-configuration quantities (primary) ------------------------
    def energy(self, lam: float) -> float:
        """Strain energy per unit reference volume W(lambda_e)."""
        raise NotImplementedError

    def second_piola(self, lam: float) -> float:
        """2nd Piola-Kirchhoff stress S = dW/dE_e, Eq. (M1)  (reference config)."""
        raise NotImplementedError

    # --- push-forwards (derived; used only where a spatial stress is needed) --
    def first_piola(self, lam: float):
        """Nominal (1st PK) stress P = lambda_e S, Eq. (M2)  (force / reference area)."""
        return lam * self.second_piola(lam)

    def cauchy(self, lam: float):
        """Cauchy (true) stress sigma = lambda_e^2 S, Eq. (M3)  (push-forward, J=1).

        This is the *spatial* stress that enters the Laplace / dead-load balance
        (``gr.geometry``) and the intramural-stress growth stimulus.  It is a
        derived quantity — the constitutive law itself lives in the reference
        configuration via ``second_piola``.
        """
        return lam**2 * self.second_piola(lam)


@dataclass(frozen=True)
class NeoHookean(MaterialLaw):
    r"""
    Incompressible neo-Hookean, Eq. (NH) — elastin (soft, mildly nonlinear).

        W_e = (c/2)(lambda_e^2 + 2/lambda_e - 3)
        S_e = c (1 - lambda_e^{-3})            (2nd PK, reference)
        sigma_e = lambda_e^2 S_e = c (lambda_e^2 - 1/lambda_e)   (Cauchy push-forward)

    Parameters
    ----------
    c : float
        Shear-modulus-like stiffness [kPa].
    """

    c: float  # [kPa]

    def energy(self, lam: float) -> float:
        return 0.5 * self.c * (lam**2 + 2.0 / lam - 3.0)

    def second_piola(self, lam: float):
        return self.c * (1.0 - lam ** (-3))


@dataclass(frozen=True)
class FungFiber(MaterialLaw):
    r"""
    Fung-type exponential fiber, Eq. (FUNG) — collagen and smooth muscle, which
    are crimped at rest and stiffen steeply once recruited (I4 = lambda_e^2):

        W = c1/(4 c2) ( exp[c2 (I4 - 1)^2] - 1 )
        S = c1 (lambda_e^2 - 1) exp[c2 (lambda_e^2 - 1)^2]      (2nd PK, reference)
        sigma = lambda_e^2 S                                    (Cauchy push-forward)

    Parameters
    ----------
    c1 : float
        Low-strain stiffness [kPa].
    c2 : float
        Dimensionless stiffening (exponential) parameter [-].
    """

    c1: float  # [kPa]
    c2: float  # [-]

    def energy(self, lam: float) -> float:
        Q = self.c2 * (lam**2 - 1.0) ** 2
        return self.c1 / (4.0 * self.c2) * (_exp(Q) - 1.0)

    def second_piola(self, lam: float):
        E4 = lam**2 - 1.0
        return self.c1 * E4 * _exp(self.c2 * E4**2)


def _exp(x):
    """np.exp with a guard so runaway aneurysm solves don't overflow.

    Works on both Python floats and NumPy arrays (the full constrained-mixture
    model sums the stress over many cohorts at once, ``gr.constrained_mixture``).
    """
    import numpy as np

    # Clip well below exp's overflow so that (polynomial factor) * exp() stays
    # finite even at the absurd stretches a runaway aneurysm solve probes.
    return np.exp(np.minimum(x, 300.0))

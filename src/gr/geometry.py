r"""
Mechanical equilibrium for the thin-walled artery.  Every theory shares this
layer.

At every instant the tissue must be in **mechanical equilibrium**: the Cauchy
stress the material *supplies* (from its deformation, via the constitutive laws)
must equal the stress the loading *requires*.  The models differ in how they
compute the supplied stress ``sigma_bar(lambda)``; this file supplies the
*required* stress and solves the balance for the current global stretch lambda.

-------------------------------------------------------------------------------
The required stress — the Laplace law
-------------------------------------------------------------------------------
Let ``lambda`` be the circumferential stretch (current mid-wall radius
r = lambda * R) and ``m = M/M_0`` the current total mass relative to
homeostasis.  Assuming incompressible constituents (growth only adds material),
the current load-bearing cross-section shrinks with stretch and grows with mass,
which gives (derivation in docs/03..06):

    artery, Laplace P r / h:  sigma_req = sigma_h * gamma * lambda**2 / m      (G2)

where ``sigma_h`` is the mixture homeostatic stress (Eq. P2) and ``gamma`` is the
current load factor (pressure_factor for hypertension; 1 for the aneurysm
scenario, whose insult acts through the material, not the load).

The quadratic power of ``lambda`` is the Laplace law: in a pressurised tube,
dilating raises wall stress, which can *drive further dilation*.  It is the
mathematical seed of aneurysm instability, and every stability result in this
course traces back to it.  See the exercise in docs/07_stability.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from scipy.optimize import brentq

from .parameters import Model


@dataclass(frozen=True)
class Geometry:
    """A loading setting: how required stress depends on stretch and mass."""

    name: str
    stress_exponent: int  # 2 for the artery (Laplace law), Eq. (G2)
    model: Model

    def required_stress(self, lam: float, mass_ratio: float, load_factor: float) -> float:
        """Stress the loading demands, Eq. (G2)."""
        return self.model.sigma_bar_h * load_factor * lam**self.stress_exponent / mass_ratio

    def equilibrium_stretch(
        self,
        supplied_stress: Callable[[float], float],
        mass_ratio: float,
        load_factor: float,
        bracket: tuple[float, float] = (0.2, 20.0),
    ) -> float | None:
        r"""
        Solve  supplied_stress(lambda) = required_stress(lambda)  for lambda.

        ``supplied_stress(lam)`` is provided by each theory (the mixture Cauchy
        stress at global stretch ``lam``, given the current natural
        configurations).  Returns ``None`` when no equilibrium exists in the
        bracket — exactly the *loss of a mechanically equilibrated state* that
        signals a runaway aneurysm.
        """

        def residual(lam: float) -> float:
            return supplied_stress(lam) - self.required_stress(lam, mass_ratio, load_factor)

        lo, hi = bracket
        f_lo, f_hi = residual(lo), residual(hi)
        if f_lo * f_hi > 0.0:
            # No sign change -> no equilibrium in the physiological range.
            return None
        return brentq(residual, lo, hi, xtol=1e-10, rtol=1e-12)

    # -- reporting helpers (for plots / tables) -------------------------------
    def radius(self, lam: float) -> float:
        """Current **mid-wall** radius [mm], a = lambda R.

        A thin-walled tube is described by a single mid-wall radius ``a`` and a
        thickness ``h`` -- exactly the two quantities the Laplace balance
        sigma = P a / h uses. ``R`` is the reference mid-wall radius.
        """
        return lam * self.model.R

    def thickness(self, lam: float, mass_ratio: float) -> float:
        """Current wall thickness [mm], h = H * m / lambda."""
        return self.model.H * mass_ratio / lam


def artery(model: Model) -> Geometry:
    """Thin-walled cylindrical artery, Laplace law — Eq. (G2)."""
    return Geometry(name="artery", stress_exponent=2, model=model)

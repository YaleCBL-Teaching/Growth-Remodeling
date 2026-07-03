r"""
Shared parameters for every model and every scenario.

The whole point of this file is that the four theories (kinematic growth, full /
homogenized / equilibrated constrained mixture) and the two geometries (1D bar,
thin-walled artery) all read the **same** numbers.  Change a value here and it
changes everywhere — so a comparison plot is always apples-to-apples.

-------------------------------------------------------------------------------
The homeostatic (set-point) trick
-------------------------------------------------------------------------------
Rather than invent a separate "target stress" for each constituent, we *derive*
it from the biology (see docs/01_biology.md §1.3): a constituent is deposited by
the cells at its **deposition stretch** ``G``.  Therefore its homeostatic stress
is simply the constitutive stress evaluated at that stretch:

        sigma_h^k  :=  sigma^k(G^k)                                        (P1)

At the homeostatic state the tissue sits at global stretch ``lambda = 1`` and
every constituent's elastic stretch equals its own ``G^k``.  This single
convention pins down all set-points from a handful of physically meaningful
inputs (stiffnesses, deposition stretches, mass fractions).

Representative values are for a large elastic artery and are in the range used
by Humphrey, Cyron, Latorre and co-workers (order-of-magnitude, teaching-grade;
not a fit to any one animal).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from .mechanics import FungFiber, MaterialLaw, NeoHookean


@dataclass(frozen=True)
class Constituent:
    r"""
    One structural constituent (elastin, collagen, or smooth muscle).

    Attributes
    ----------
    name : str
    phi0 : float
        Reference **mass fraction** at homeostasis (the phi's sum to 1).
    G : float
        Deposition (pre-)stretch — the elastic stretch at which new material is
        laid down, and hence the homeostatic elastic stretch, Eq. (P1).
    law : MaterialLaw
        Constitutive law, from ``gr.mechanics``.
    k_d : float
        Mass **removal rate** [1/day].  Its reciprocal 1/k_d is the mean
        lifetime of the constituent.  Elastin ~ 0 (never renewed); collagen and
        smooth muscle turn over in weeks-to-months.
    gain : float
        Mechano-sensitivity ``K_sigma`` of mass production to stress deviation
        (dimensionless).  Larger gain = a stiffer, faster corrective response.
    degradable : bool
        Whether an *insult* can actively destroy this constituent (elastin, in
        the aneurysm scenario).
    """

    name: str
    phi0: float
    G: float
    law: MaterialLaw
    k_d: float
    gain: float
    degradable: bool = False

    @property
    def sigma_h(self) -> float:
        """Homeostatic constituent stress sigma_h^k = sigma^k(G^k), Eq. (P1)."""
        return self.law.stress_cauchy(self.G)


# -----------------------------------------------------------------------------
# Default arterial constituents.  Elastin is soft and NON-renewable (k_d = 0);
# collagen and smooth muscle are stiffer, pre-stretched less, and turn over.
# -----------------------------------------------------------------------------
def default_constituents() -> list[Constituent]:
    return [
        Constituent(
            name="elastin",
            phi0=0.30,
            G=1.40,                       # elastin is laid down highly pre-stretched
            law=NeoHookean(c=90.0),       # kPa, soft rubber-like
            k_d=0.0,                      # never renewed in the adult
            gain=0.0,                     # no stress-mediated production
            degradable=True,              # the aneurysm insult destroys elastin
        ),
        Constituent(
            name="collagen",
            phi0=0.35,
            G=1.08,                       # deposited under mild tension
            law=FungFiber(c1=250.0, c2=8.0),
            k_d=1.0 / 20.0,               # ~20-day lifetime (small-vessel value; aorta ~70 d)
            gain=1.0,                     # mechano-sensitivity K_sigma (order 1)
        ),
        Constituent(
            name="smc",                   # smooth muscle (passive part only here)
            phi0=0.35,
            G=1.20,
            law=FungFiber(c1=120.0, c2=3.0),
            k_d=1.0 / 20.0,
            gain=1.0,
        ),
    ]


@dataclass(frozen=True)
class Model:
    r"""
    A complete, self-consistent problem definition shared by all theories.

    Reference geometry is chosen so the thin-walled Laplace balance holds *exactly*
    at homeostasis (see ``gr.geometry``):

        P_h * r / h = sigma_bar_h      at   lambda = 1, mass = mass_0            (P2)

    so the reference thickness ``H`` is derived, not guessed.
    """

    constituents: list[Constituent] = field(default_factory=default_constituents)
    P_h: float = 13.3          # homeostatic luminal pressure [kPa] (~100 mmHg)
    R: float = 1.0             # reference inner radius [mm]

    # ---- derived homeostatic quantities -------------------------------------
    @property
    def sigma_bar_h(self) -> float:
        """Mixture homeostatic Cauchy stress = sum_k phi0^k sigma_h^k."""
        return sum(c.phi0 * c.sigma_h for c in self.constituents)

    @property
    def H(self) -> float:
        """Reference wall thickness from the homeostatic Laplace balance, Eq. (P2)."""
        return self.P_h * self.R / self.sigma_bar_h

    def by_name(self, name: str) -> Constituent:
        for c in self.constituents:
            if c.name == name:
                return c
        raise KeyError(name)

    # ---- convenience for exercises ------------------------------------------
    def with_constituent(self, name: str, **changes) -> "Model":
        """Return a copy of the model with one constituent's fields changed.

        Example (used throughout the exercises)::

            model2 = model.with_constituent("collagen", gain=2.0)
        """
        new = [replace(c, **changes) if c.name == name else c for c in self.constituents]
        return replace(self, constituents=new)


# -----------------------------------------------------------------------------
# Insults — the two canonical drivers from docs/01_biology.md §1.5.
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class Insult:
    r"""
    A time-dependent perturbation applied to the homeostatic tissue.

    Parameters
    ----------
    pressure_factor : float
        Multiplies ``P_h`` for t >= t_on (hypertension: e.g. 1.5).
    elastin_surviving : float
        Long-time surviving fraction of elastin for t >= t_on (aneurysm:
        e.g. 0.3 keeps 30% of elastin).
    t_on : float
        Onset time [day] of the step.
    ramp : float
        Ramp duration [day] over which the step is applied (a small positive
        ramp avoids a numerical shock; set 0 for an instantaneous step).
    """

    pressure_factor: float = 1.0
    elastin_surviving: float = 1.0
    t_on: float = 0.0
    ramp: float = 1.0

    def _frac(self, t: float) -> float:
        if t <= self.t_on:
            return 0.0
        if self.ramp <= 0.0:
            return 1.0
        return min(1.0, (t - self.t_on) / self.ramp)

    def pressure(self, P_h: float, t: float) -> float:
        """Luminal pressure at time ``t``."""
        f = self._frac(t)
        return P_h * (1.0 + f * (self.pressure_factor - 1.0))

    def elastin_fraction(self, t: float) -> float:
        """Fraction of the *original* elastin still present at time ``t``."""
        f = self._frac(t)
        return 1.0 + f * (self.elastin_surviving - 1.0)


# Handy presets used by the exercises/solutions.
HYPERTENSION = Insult(pressure_factor=1.5, t_on=1.0, ramp=1.0)
ANEURYSM = Insult(elastin_surviving=0.30, t_on=1.0, ramp=10.0)

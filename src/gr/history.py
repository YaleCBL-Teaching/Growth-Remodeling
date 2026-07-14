r"""
A tiny container for a simulation's time history, shared by all four theories so
that plotting and comparison code is generic.

Every ``simulate(...)`` in this package returns a :class:`Result`.  Standard
fields let the plotting helpers overlay any theory against any other without
special-casing.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def _tail_steady(arr: np.ndarray, frac: float = 0.1, tol: float = 5e-3) -> bool:
    """True if ``arr`` barely changes over its final ``frac`` of samples.

    Used to tell a genuinely *adapted* run (state has settled) from one that only
    *looks* adapted because the stress is held near the set-point by mass that is
    still growing without bound -- a slow runaway that never trips the hard
    ``lam_runaway`` cutoff within the simulated window.
    """
    a = np.asarray(arr, dtype=float)
    a = a[np.isfinite(a)]
    if a.size < 3:
        return True
    i0 = max(0, int(a.size * (1.0 - frac)) - 1)
    return abs(a[-1] - a[i0]) <= tol * max(abs(a[-1]), 1e-9)


@dataclass
class Result:
    """Time history of one G&R simulation."""

    theory: str                       # e.g. "homogenized CMM"
    setting: str                      # "artery"
    sigma_h: float                    # mixture homeostatic stress [kPa] (set-point)
    t: np.ndarray                     # time [day]
    lam: np.ndarray                   # global stretch [-]
    mass: np.ndarray                  # total mass ratio M/M_0 [-]
    sigma: np.ndarray                 # mixture wall Cauchy stress [kPa]
    radius: np.ndarray                # mid-wall radius [mm]
    thickness: np.ndarray             # wall thickness [mm]
    masses: dict[str, np.ndarray] = field(default_factory=dict)  # per-constituent M^k/M_0
    # per-constituent stress normalised by its OWN homeostatic value, sigma^k/sigma_h^k
    # (returns to 1 when a constituent is back at its deposition stretch G^k)
    stresses: dict[str, np.ndarray] = field(default_factory=dict)
    diverged: bool = False            # True if the run lost equilibrium (runaway)

    @property
    def sigma_norm(self) -> np.ndarray:
        r"""Stress normalised by the homeostatic set-point, sigma / sigma_h.

        This is *the* quantity to watch: it returns to 1 when the tissue has
        adapted, and runs away from 1 when it has not.
        """
        return self.sigma / self.sigma_h

    @property
    def converged(self) -> bool:
        """True if the run actually settled to a steady state.

        ``diverged`` catches only the hard runaway (stretch hit the cutoff); this
        also flags the *slow* runaway, where stress sits near the set-point but the
        stretch and mass are still climbing at the end of the window.
        """
        if self.diverged:
            return False
        return _tail_steady(self.lam) and _tail_steady(self.mass)

    def final(self) -> dict:
        """Last recorded state, as a plain dict (handy for tables)."""
        return {
            "lam": float(self.lam[-1]),
            "mass": float(self.mass[-1]),
            "sigma_norm": float(self.sigma_norm[-1]),
            "diverged": self.diverged,
        }

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


@dataclass
class Result:
    """Time history of one G&R simulation."""

    theory: str                       # e.g. "homogenized CMM"
    setting: str                      # "bar" or "artery"
    sigma_h: float                    # mixture homeostatic stress [kPa] (set-point)
    t: np.ndarray                     # time [day]
    lam: np.ndarray                   # global stretch [-]
    mass: np.ndarray                  # total mass ratio M/M_0 [-]
    sigma: np.ndarray                 # mixture Cauchy stress [kPa]
    radius: np.ndarray                # inner radius (artery) / length (bar) [mm]
    thickness: np.ndarray             # wall thickness [mm] (artery)
    masses: dict[str, np.ndarray] = field(default_factory=dict)  # per-constituent M^k/M_0
    diverged: bool = False            # True if the run lost equilibrium (runaway)

    @property
    def sigma_norm(self) -> np.ndarray:
        r"""Stress normalised by the homeostatic set-point, sigma / sigma_h.

        This is *the* quantity to watch: it returns to 1 when the tissue has
        adapted, and runs away from 1 when it has not.
        """
        return self.sigma / self.sigma_h

    def final(self) -> dict:
        """Last recorded state, as a plain dict (handy for tables)."""
        return {
            "lam": float(self.lam[-1]),
            "mass": float(self.mass[-1]),
            "sigma_norm": float(self.sigma_norm[-1]),
            "diverged": self.diverged,
        }

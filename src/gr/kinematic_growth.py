r"""
Theory 1 of 4 — KINEMATIC GROWTH  (Rodriguez, Hoger & McCulloch, 1994).

-------------------------------------------------------------------------------
The idea
-------------------------------------------------------------------------------
Kinematic growth treats the wall as a **single homogeneous material** — there are
no constituents, no mass fractions, no turnover and no per-constituent natural
configurations.  That is the whole point (and the limitation) of the theory: it
is the simplest continuum description of growth, to be contrasted with the
constrained-mixture theories that *do* resolve constituents.

Split the (scalar) deformation gradient into an elastic and a stress-free
**growth** part,

        F  =  Fe . Fg ,                                                   (KG1)

with only ``Fe`` carrying stress.  For an artery, growth is anisotropic
**thickening**: the wall grows radially (a single thickening variable ``theta``,
= the mass ratio M/M_0), which does not change the circumferential elastic
stretch ``lambda``.

The single material carries the homeostatic wall stress ``sigma_h = P_h R / H``
(a tissue-level quantity from the Laplace balance, not built from constituents) at
the homeostatic state (lambda = 1).  Its incremental response is a single
stiffening law calibrated to the tissue's homeostatic stiffness ``b``:

        sigma(lambda) = s * sigma_h * exp[ b (lambda - 1) ]              (KG2)

Here ``s <= 1`` is a damage factor: the elastin-loss (aneurysm) insult is
represented, for this single material, as an equivalent loss of load-bearing
capacity (a single number), since a one-material theory has no elastin to remove.

Growth is driven to null the wall-stress deviation from the set-point (a
first-order stress-dependent growth law; production proportional to current mass):

        d(theta)/dt = k_g * theta * ( sigma / sigma_h - 1 )              (KG3)

-------------------------------------------------------------------------------
What to learn (docs/03_kinematic_growth.md)
-------------------------------------------------------------------------------
The set-point ``sigma_h`` is *prescribed*: growth restores the homeostatic wall
stress **by construction** (or runs away).  But because it is one material,
kinematic growth cannot resolve which constituent carries what, nor remodel them
individually — exactly the information the constrained-mixture theories add.
"""
from __future__ import annotations

import numpy as np

from .geometry import Geometry
from .history import Result
from .parameters import Insult


def simulate(
    geom: Geometry,
    insult: Insult,
    *,
    k_g: float = 0.05,               # growth-rate gain [1/day], Eq. (KG3)
    tissue_stiffness: float | None = None,   # b in (KG2); None -> calibrate to the tissue
    t_end: float = 2000.0,           # [day]
    dt: float = 1.0,                 # [day]
    lam_runaway: float = 8.0,
) -> Result:
    """Integrate kinematic growth (single material) for the given loading."""
    model = geom.model
    sigma_h = model.sigma_bar_h       # homeostatic wall stress P_h R / H (tissue-level)

    # --- a single equivalent material, calibrated ONCE to the tissue ---------
    # (the constituents define what the tissue *is* — its homeostatic stress and
    #  stiffness — but they are not part of the kinematic theory itself.)
    def _tissue_homeostatic(lam: float) -> float:
        return sum(c.phi0 * c.law.stress_cauchy(c.G * lam) for c in model.constituents)

    if tissue_stiffness is None:
        eps = 1e-4
        b = (_tissue_homeostatic(1 + eps) - _tissue_homeostatic(1 - eps)) / (2 * eps) / sigma_h
    else:
        b = tissue_stiffness
    elastin = model.by_name("elastin")
    f_elastin = elastin.phi0 * elastin.sigma_h / sigma_h    # elastin's homeostatic stress share

    def sigma_tissue(lam: float, s: float) -> float:
        return s * sigma_h * np.exp(b * (lam - 1.0))

    nsteps = int(round(t_end / dt))
    t = np.zeros(nsteps + 1)
    theta = 1.0                       # thickening growth variable; homeostasis: theta = 1
    out = {k: np.zeros(nsteps + 1) for k in ("lam", "mass", "sigma", "r", "h")}
    diverged = False

    for i in range(nsteps + 1):
        ti = i * dt
        t[i] = ti
        gamma = insult.pressure(model.P_h, ti) / model.P_h
        # elastin loss -> equivalent weakening of the single material
        s_eff = 1.0 - (1.0 - insult.elastin_fraction(ti)) * f_elastin

        # (i) mechanical equilibrium: sigma_tissue(lam) = required(lam), mass = theta
        lam = geom.equilibrium_stretch(
            lambda L: sigma_tissue(L, s_eff), mass_ratio=theta, load_factor=gamma
        )
        if lam is None or lam > lam_runaway:
            diverged = True
            for key in out:
                out[key][i:] = out[key][i - 1] if i > 0 else np.nan
            t[i:] = np.linspace(ti, t_end, nsteps + 1 - i)
            break

        sig = sigma_tissue(lam, s_eff)
        out["lam"][i] = lam
        out["mass"][i] = theta
        out["sigma"][i] = sig
        out["r"][i] = geom.radius(lam)
        out["h"][i] = geom.thickness(lam, theta)

        # (ii) advance growth one step, Eq. (KG3)
        if i < nsteps:
            theta = max(theta + dt * k_g * theta * (sig / sigma_h - 1.0), 1e-6)

    return Result(
        theory="kinematic growth",
        setting=geom.name,
        sigma_h=sigma_h,
        t=t,
        lam=out["lam"],
        mass=out["mass"],
        sigma=out["sigma"],
        radius=out["r"],
        thickness=out["h"],
        masses={"grown_volume": out["mass"]},   # single material: one grown volume, no constituents
        diverged=diverged,
    )

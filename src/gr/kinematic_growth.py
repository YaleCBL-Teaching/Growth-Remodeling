r"""
Theory 1 of 4 — KINEMATIC GROWTH  (Rodriguez, Hoger & McCulloch, 1994).

-------------------------------------------------------------------------------
The idea
-------------------------------------------------------------------------------
Postulate a multiplicative split of the deformation gradient into an elastic part
and a stress-free **growth** part:

        F  =  Fe . Fg                                                     (KG1)

Only ``Fe`` (grown state -> current state) stores energy and produces stress;
``Fg`` (reference -> grown state) is a stress-free change of the natural volume —
it *is* the growth.  For an artery, growth is **anisotropic thickening**: the
wall grows in the radial direction (adding material through the thickness) while
the circumferential elastic stretch of the material is unchanged by growth.  We
capture this with a single scalar thickening variable ``theta`` (= the mass
ratio; a transversely isotropic growth tensor Fg = I + (theta-1) e_r (x) e_r):

        mass ratio  M/M_0 = theta,     constituent stretch = G^k * lambda   (KG2)

where ``lambda`` is the (circumferential) tissue stretch and G^k the deposition
prestretch (at homeostasis theta = 1, lambda = 1, so the constituent sits at G^k,
giving sigma_h^k).  Crucially the whole mixture shares one growth variable — there
is **no** individual constituent turnover or remodeling of natural configurations.

Growth is driven to null the tissue-stress deviation from the set-point (a
first-order form of the classic stress-dependent growth law; production taken
proportional to current mass so that theta can settle anywhere):

        d(theta)/dt = k_g * theta * ( sigma_bar / sigma_bar_h - 1 )        (KG3)

-------------------------------------------------------------------------------
What to learn (docs/03_kinematic_growth.md)
-------------------------------------------------------------------------------
The set-point sigma_bar_h is *prescribed*: wherever growth settles, it settles at
homeostasis **by construction**.  The only two outcomes are:

  * it converges to the prescribed homeostatic stress (a stable fixed point
    exists), **or**
  * it grows without bound (no stable fixed point).

Which one occurs is set by the mechanical feedback — the exponent in the
required-stress law (``gr.geometry``): the bar (exponent 1) is always
self-limiting; the artery (exponent 2, Laplace) can lose stability for a strong
enough insult.  But kinematic growth cannot *predict* mechanobiological stability
from tissue turnover — that is what the mixture theories add.
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
    k_g: float = 0.05,        # growth-rate gain [1/day], Eq. (KG3)
    t_end: float = 2000.0,    # [day]
    dt: float = 1.0,          # [day]
    lam_runaway: float = 8.0,  # stop if the tissue dilates past this stretch
) -> Result:
    """Integrate kinematic growth for the given loading and insult."""
    model = geom.model
    cons = model.constituents

    def sigma_bar(lam: float, elastin_frac: float) -> float:
        """Mixture Cauchy stress at tissue stretch ``lam``, Eq. (KG2) + rule of mixtures.

        Growth is radial (thickening) and does not enter the circumferential
        elastic stretch, so the constituent stretch is simply G^k * lambda.
        """
        total = 0.0
        for c in cons:
            phi = c.phi0 * (elastin_frac if c.name == "elastin" else 1.0)
            total += phi * c.law.stress_cauchy(c.G * lam)
        return total

    nsteps = int(round(t_end / dt))
    t = np.zeros(nsteps + 1)
    theta = 1.0                      # thickening growth variable; homeostasis: theta = 1
    out = {k: np.zeros(nsteps + 1) for k in ("lam", "mass", "sigma", "r", "h")}
    diverged = False

    for i in range(nsteps + 1):
        ti = i * dt
        t[i] = ti
        gamma = insult.pressure(model.P_h, ti) / model.P_h
        ef = insult.elastin_fraction(ti)

        # (i) mechanical equilibrium: solve sigma_bar(lam) = required(lam), mass = theta
        lam = geom.equilibrium_stretch(
            lambda L: sigma_bar(L, ef), mass_ratio=theta, load_factor=gamma
        )
        if lam is None or lam > lam_runaway:
            diverged = True
            for key in out:
                out[key][i:] = out[key][i - 1] if i > 0 else np.nan
            t[i:] = np.linspace(ti, t_end, nsteps + 1 - i)
            break

        sig = sigma_bar(lam, ef)
        out["lam"][i] = lam
        out["mass"][i] = theta
        out["sigma"][i] = sig
        out["r"][i] = geom.radius(lam)
        out["h"][i] = geom.thickness(lam, theta)

        # (ii) advance growth one step, Eq. (KG3)
        if i < nsteps:
            theta = theta + dt * k_g * theta * (sig / model.sigma_bar_h - 1.0)
            theta = max(theta, 1e-6)

    return Result(
        theory="kinematic growth",
        setting=geom.name,
        sigma_h=model.sigma_bar_h,
        t=t,
        lam=out["lam"],
        mass=out["mass"],
        sigma=out["sigma"],
        radius=out["r"],
        thickness=out["h"],
        masses={"grown_volume": out["mass"]},
        diverged=diverged,
    )

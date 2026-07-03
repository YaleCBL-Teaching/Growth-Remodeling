r"""
Theory 3 of 4 — HOMOGENIZED CONSTRAINED MIXTURE MODEL
(Cyron, Aydin & Humphrey, 2016; Braeu, Seitz, Aydin & Cyron, 2017).

The full model (Theory 2) is faithful but expensive: it stores every past
cohort.  The homogenized model does **temporal homogenization** — it replaces the
whole deposition history of a constituent by a *single evolving mean natural
configuration*.  Two ordinary differential equations per constituent then take
the place of the heredity integral.  No history to store; cost is O(N), not
O(N^2).

-------------------------------------------------------------------------------
Governing equations (docs/05_homogenized_cmm.md)
-------------------------------------------------------------------------------
For each turnover constituent k we evolve its mass M^k and a mean natural stretch
lambda_n^k.  Its elastic stretch is

    lambda_e^k = lambda / lambda_n^k                                       (HC1)

**Growth (mass).**  Production is proportional to current mass (so mass is free
to settle anywhere once stress is restored) and driven by the stress deviation —
the Cyron/Braeu law d(rho)/dt = rho k_sigma (sigma - sigma_h)/sigma_h:

    dM^k/dt = M^k * (K_sigma^k k_d^k) * ( sigma^k/sigma_h^k - 1 )           (HC2)

**Remodeling (natural configuration).**  New mass is deposited at the deposition
stretch G^k, i.e. with mean natural stretch lambda/G^k; old mass (at the current
lambda_n^k) is removed.  Mixing the two at the turnover rate gives

    d(lambda_n^k)/dt = (m^k / M^k) ( lambda/G^k - lambda_n^k ),
    with production rate  m^k = k_d^k M^k Upsilon^k                        (HC3)

This is the temporal homogenization of the full cohort integral (CM4).  Holding
lambda fixed, it makes the constituent stress **relax exponentially toward its
homeostatic value sigma_h^k** with a time constant ~ 1/k_d — exactly Cyron 2016's
"mechanical analog" (a Maxwell spring-dashpot in parallel with a homeostatic
motor).  At steady state lambda_n^k -> lambda/G^k, so lambda_e^k -> G^k and
sigma^k -> sigma_h^k.

-------------------------------------------------------------------------------
What to learn (docs/05, docs/07)
-------------------------------------------------------------------------------
The homogenized model tracks the **full model's time trajectory closely** at a
fraction of the cost — that is its whole reason for existing.  The exercises ask
you to overlay the two and see how well they agree.
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
    t_end: float = 2000.0,   # [day]
    dt: float = 1.0,         # [day]
    lam_runaway: float = 8.0,
) -> Result:
    """Integrate the homogenized CMM (two ODEs per turnover constituent)."""
    model = geom.model
    turnover = [c for c in model.constituents if c.k_d > 0.0]
    elastin = model.by_name("elastin")

    # State: mass M^k and mean natural stretch lambda_n^k.
    # Homeostatic start: lambda_n^k = 1/G^k so that lambda_e^k = 1*G^k = G^k at lambda = 1.
    M = {c.name: c.phi0 for c in turnover}
    lam_n = {c.name: 1.0 / c.G for c in turnover}

    N = int(round(t_end / dt))
    t = np.arange(N + 1) * dt
    out = {k: np.zeros(N + 1) for k in ("lam", "mass", "sigma", "r", "h")}
    masses_hist = {c.name: np.zeros(N + 1) for c in model.constituents}
    diverged = False

    for i in range(N + 1):
        ti = t[i]
        gamma = insult.pressure(model.P_h, ti) / model.P_h
        ef = insult.elastin_fraction(ti)
        M_elastin = elastin.phi0 * ef
        M_tot = M_elastin + sum(M.values())

        # supplied mixture stress vs global stretch, Eq. (HC1) + rule of mixtures
        def sigma_bar(lam: float) -> float:
            total = M_elastin * elastin.law.stress_cauchy(elastin.G * lam)
            for c in turnover:
                total += M[c.name] * c.law.stress_cauchy(lam / lam_n[c.name])
            return total / M_tot

        lam = geom.equilibrium_stretch(sigma_bar, mass_ratio=M_tot, load_factor=gamma)
        if lam is None or lam > lam_runaway:
            diverged = True
            for key in out:
                out[key][i:] = out[key][i - 1] if i > 0 else np.nan
            for nm in masses_hist:
                masses_hist[nm][i:] = masses_hist[nm][i - 1] if i > 0 else np.nan
            break

        out["lam"][i] = lam
        out["mass"][i] = M_tot
        out["sigma"][i] = sigma_bar(lam)
        out["r"][i] = geom.radius(lam)
        out["h"][i] = geom.thickness(lam, M_tot)
        masses_hist["elastin"][i] = M_elastin
        for c in turnover:
            masses_hist[c.name][i] = M[c.name]

        # advance the ODEs one explicit step, Eqs. (HC2)-(HC3)
        #
        # Growth is driven by the TISSUE (mixture) stress deviation, so all
        # constituents grow in step and the tissue returns to sigma_bar_h -- this
        # is what makes the transient converge to the *equilibrated* solution
        # (gr.equilibrated_cmm).  Remodeling separately drives each constituent's
        # natural configuration toward its deposition stretch G^k.
        if i < N:
            dev = out["sigma"][i] / model.sigma_bar_h - 1.0        # tissue stress deviation
            for c in turnover:
                upsilon = max(0.0, 1.0 + c.gain * dev)             # production stimulus
                prod_rate = c.k_d * M[c.name] * upsilon            # m^k, Eq. (HC3)
                dM = M[c.name] * (c.gain * c.k_d) * dev            # growth, Eq. (HC2)
                dlam_n = (prod_rate / M[c.name]) * (lam / c.G - lam_n[c.name])
                M[c.name] += dt * dM
                lam_n[c.name] += dt * dlam_n

    return Result(
        theory="homogenized CMM",
        setting=geom.name,
        sigma_h=model.sigma_bar_h,
        t=t,
        lam=out["lam"],
        mass=out["mass"],
        sigma=out["sigma"],
        radius=out["r"],
        thickness=out["h"],
        masses=masses_hist,
        diverged=diverged,
    )

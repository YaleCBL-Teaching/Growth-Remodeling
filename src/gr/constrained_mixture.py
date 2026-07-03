r"""
Theory 2 of 4 — FULL CONSTRAINED MIXTURE MODEL  (Humphrey & Rajagopal, 2002;
Baek, Valentin, Humphrey; Latorre & Humphrey).

This is the "gold standard" the other mixture theories approximate.  It tracks
the **entire deposition history**: every past cohort of collagen / smooth muscle
keeps its own natural configuration and survival fraction, and the current stress
is a heredity (history) integral over all of them.

-------------------------------------------------------------------------------
Governing equations (docs/04_constrained_mixture.md; FSGe / Latorre-Humphrey)
-------------------------------------------------------------------------------
Mass balance for a turnover constituent k (elastin does not turn over):

    M^k(t) = M^k(0) q^k(t,0) + \int_0^t m^k(tau) q^k(t,tau) dtau            (CM1)

with a first-order (Poisson) survival function of removal rate k_d^k:

    q^k(t,tau) = exp[ -k_d^k (t - tau) ]                                    (CM2)

Mass is produced in proportion to the current mass, modulated by a stress
stimulus (production balances removal at homeostasis, so Upsilon = 1 there).  The
stimulus senses the TISSUE (mixture) intramural stress sigma_bar relative to its
homeostatic value -- so all constituents grow together to restore tissue
homeostasis (this is what makes the transient converge to the equilibrated state,
gr.equilibrated_cmm):

    m^k(tau) = k_d^k M^k(tau) * Upsilon(tau),
    Upsilon(tau) = 1 + K_sigma^k ( sigma_bar(tau)/sigma_bar_h - 1 )         (CM3)

A cohort of k deposited at time tau is laid down at the deposition stretch G^k;
evaluated at the current time t its elastic stretch is (constrained mixture:
constituents deform together with the tissue stretch lambda)

    lambda_e^{k}(t;tau) = G^k * lambda(t) / lambda(tau)                     (CM4)

The mixture Cauchy stress is the mass-weighted heredity integral of the
constituent stresses (rule of mixtures):

    sigma_bar(t) = (1/M_tot) * sum_k [ M^k(0) q^k(t,0) sigma^k(G^k lambda/lambda_0)
                     + \int_0^t m^k(tau) q^k(t,tau) sigma^k(G^k lambda/lambda(tau)) dtau ] (CM5)

-------------------------------------------------------------------------------
What to learn (docs/07_stability.md)
-------------------------------------------------------------------------------
Unlike kinematic growth, stability here is *not* prescribed — it emerges from the
turnover dynamics.  For a mild insult the tissue adapts to a new equilibrium; for
a strong enough insult (large elastin loss, low gain) no equilibrium is reached
and the artery dilates without bound.  **Stability depends on the insult.**

Implementation note: the history integrals are discretised as sums over stored
cohorts (an explicit, readable scheme).  Cost grows like O(N^2) in the number of
time steps — which is exactly why the homogenized model (Theory 3) exists.
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
    t_end: float = 2000.0,      # [day]
    dt: float = 1.0,            # [day]  (explicit heredity integral; smaller dt = more accurate)
    lam_runaway: float = 8.0,
) -> Result:
    """Integrate the full constrained-mixture model (heredity integrals)."""
    model = geom.model
    turnover = [c for c in model.constituents if c.k_d > 0.0]
    elastin = model.by_name("elastin")

    N = int(round(t_end / dt))
    t = np.arange(N + 1) * dt

    # Per-turnover-constituent cohort book-keeping.  cohort j was produced at
    # time t[j] at global stretch lam_dep[j]; its production rate is m_prod[k][j].
    lam_dep = np.ones(N + 1)                                   # global stretch history lambda(tau)
    m_prod = {c.name: np.zeros(N + 1) for c in turnover}       # production rate m^k(tau)
    M0 = {c.name: c.phi0 for c in turnover}                    # initial mass (M_tot0 = 1)

    out = {k: np.zeros(N + 1) for k in ("lam", "mass", "sigma", "r", "h")}
    masses_hist = {c.name: np.zeros(N + 1) for c in model.constituents}
    diverged = False

    for i in range(N + 1):
        ti = t[i]
        gamma = insult.pressure(model.P_h, ti) / model.P_h
        ef = insult.elastin_fraction(ti)

        # --- current masses via the heredity integral, Eqs. (CM1)-(CM2) -------
        # cohort masses (surviving) for j = 0..i-1 : m^k(t_j) exp(-k_d (t_i - t_j)) dt
        M = {}
        cohort_mass = {}  # surviving mass of each past cohort (for the stress sum)
        for c in turnover:
            j = np.arange(i)                       # past cohorts 0..i-1
            surv = np.exp(-c.k_d * (ti - t[j]))
            # Exact weight for a piecewise-constant production rate over one step:
            # integral of exp(-k_d(t-s)) ds over [t_j, t_j+dt] = surv * (e^{k_d dt}-1)/k_d.
            # (Using this instead of the naive 'dt' removes the O(k_d dt) bias, so the
            #  discrete steady state lands exactly on sigma_bar_h -- see docs/04.)
            w = (np.exp(c.k_d * dt) - 1.0) / c.k_d
            cm = m_prod[c.name][:i] * surv * w
            init = M0[c.name] * np.exp(-c.k_d * ti)   # surviving initial cohort, q^k(t,0)
            M[c.name] = init + cm.sum()
            cohort_mass[c.name] = (init, cm)          # keep split for the stress integral
        M_elastin = elastin.phi0 * ef                 # elastin: no turnover, only degradation
        M_tot = M_elastin + sum(M.values())
        mass_ratio = M_tot                            # M_tot0 = 1

        # --- supplied mixture stress as a function of global stretch, Eq. (CM5)
        def sigma_bar(lam: float) -> float:
            total = M_elastin * elastin.law.stress_cauchy(elastin.G * lam)   # elastin cohort (born at lam=1)
            for c in turnover:
                init, cm = cohort_mass[c.name]
                total += init * c.law.stress_cauchy(c.G * lam / lam_dep[0])
                if i > 0:
                    total += float((cm * c.law.stress_cauchy(c.G * lam / lam_dep[:i])).sum())
            return total / M_tot

        # --- mechanical equilibrium: solve sigma_bar(lam) = required(lam) -----
        lam = geom.equilibrium_stretch(sigma_bar, mass_ratio=mass_ratio, load_factor=gamma)
        if lam is None or lam > lam_runaway:
            diverged = True
            for key in out:
                out[key][i:] = out[key][i - 1] if i > 0 else np.nan
            for nm in masses_hist:
                masses_hist[nm][i:] = masses_hist[nm][i - 1] if i > 0 else np.nan
            break

        out["lam"][i] = lam
        out["mass"][i] = mass_ratio
        out["sigma"][i] = sigma_bar(lam)
        out["r"][i] = geom.radius(lam)
        out["h"][i] = geom.thickness(lam, mass_ratio)
        masses_hist["elastin"][i] = M_elastin
        for c in turnover:
            masses_hist[c.name][i] = M[c.name]

        # --- close the loop: tissue stress -> production for THIS step ---------
        # (explicit: this cohort's production enters the mass of later steps)
        if i < N:
            lam_dep[i] = lam
            dev = out["sigma"][i] / model.sigma_bar_h - 1.0        # tissue stress deviation
            for c in turnover:
                upsilon = 1.0 + c.gain * dev                       # stimulus, Eq. (CM3)
                m_prod[c.name][i] = max(0.0, c.k_d * M[c.name] * upsilon)

    return Result(
        theory="full CMM",
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

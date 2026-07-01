"""
Shared helpers for the teacher figures: build the seminar model and run all four
theories on a scenario.  (Students don't need this file; it just keeps the figure
scripts short and consistent.)
"""
from __future__ import annotations

from gr import (
    Model,
    artery,
    bar,
    constrained_mixture,
    equilibrated_cmm,
    homogenized_cmm,
    kinematic_growth,
)

# The default Model already carries the tuned seminar parameters.
SEMINAR_MODEL = Model()


def run_all(geom, insult, *, t_end: float = 2000.0, cmm_dt: float = 1.0):
    """Run the three transient theories + solve the equilibrated one.

    Returns (results_list, equilibrium) where results_list is ordered
    [kinematic, full CMM, homogenized CMM] and equilibrium is the Equilibrium.
    ``cmm_dt`` sets the (O(N^2)) full-CMM time step; the fixed point is
    dt-independent, so a coarser step is fine for long runs.
    """
    results = [
        kinematic_growth.simulate(geom, insult, t_end=t_end),
        constrained_mixture.simulate(geom, insult, t_end=t_end, dt=cmm_dt),
        homogenized_cmm.simulate(geom, insult, t_end=t_end),
    ]
    equilibrium = equilibrated_cmm.solve(geom, insult)
    return results, equilibrium

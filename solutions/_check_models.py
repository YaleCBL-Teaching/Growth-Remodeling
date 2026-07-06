"""
Quick numerical self-check of the four models (no plots).  Asserts the key
qualitative behaviours the seminar relies on, so you can tell immediately if a
parameter change broke something.

Run:  uv run python solutions/_check_models.py
"""
from __future__ import annotations

from gr import (
    HYPERTENSION,
    Insult,
    artery,
    constrained_mixture,
    equilibrated_cmm,
    homogenized_cmm,
    kinematic_growth,
)

from _scenarios import SEMINAR_MODEL


def check(msg, cond):
    print(f"[{'OK ' if cond else 'FAIL'}] {msg}")
    assert cond, msg


def main() -> None:
    art = artery(SEMINAR_MODEL)

    # 1. Homeostasis is a fixed point: no insult -> nothing changes.
    quiet = Insult()
    r = homogenized_cmm.simulate(art, quiet, t_end=500)
    check("no insult: stretch stays ~1", abs(r.lam[-1] - 1.0) < 1e-3)
    check("no insult: mass stays ~1", abs(r.mass[-1] - 1.0) < 1e-3)

    # 2. Hypertension: every theory restores tissue stress toward homeostatic.
    for mod in (kinematic_growth, constrained_mixture, homogenized_cmm):
        rr = mod.simulate(art, HYPERTENSION, t_end=2500)
        check(f"{rr.theory}: HTN restores stress (<4%)",
              abs(rr.sigma_norm[-1] - 1.0) < 0.04 and not rr.diverged)
        check(f"{rr.theory}: HTN thickens the wall", rr.mass[-1] > 1.2)

    # 3. Equilibrated matches the homogenized transient for a mild insult.
    mild = Insult(elastin_surviving=0.4, t_on=1, ramp=10)
    e = equilibrated_cmm.solve(art, mild)
    rh = homogenized_cmm.simulate(art, mild, t_end=4000)
    check("equilibrated exists for mild aneurysm", e.exists)
    check("equilibrated matches transient (<2%)", abs(rh.lam[-1] - e.lam) < 0.02)

    # 4. Severe insult -> no equilibrium exists (and the transient dilates a lot).
    severe = Insult(elastin_surviving=0.02, t_on=1, ramp=10)
    es = equilibrated_cmm.solve(art, severe)
    rs = homogenized_cmm.simulate(art, severe, t_end=8000)
    check("no equilibrium for severe aneurysm", not es.exists)
    check("severe aneurysm dilates strongly", rs.lam[-1] > 1.8)

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()

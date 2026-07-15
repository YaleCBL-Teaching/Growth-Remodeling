"""
TEACHER video generator — an animated twin of each simulation figure.

Every video is built from the SAME simulation results as the corresponding
static figure (via ``gr.animation``), so the numbers always match.  Each shows a
deforming vessel tinted by stress, the insult over time (so the immediate elastic
jump is separated from the slow G&R), and the response curves drawn live.

Run:  uv run python solutions/make_all_videos.py
      uv run python solutions/make_all_videos.py --gif      # GIFs for inline docs

Output: docs/videos/*.mp4  (or *.gif with --gif)

Non-time figures (fig00 setup, fig00 constitutive, and the parameter-sweep panels
of fig04/fig05) have no "live" analogue and are intentionally left as figures.
"""
from __future__ import annotations

import sys

from gr import (
    ANEURYSM,
    HYPERTENSION,
    Insult,
    artery,
    constrained_mixture,
    equilibrated_cmm,
    homogenized_cmm,
    kinematic_growth,
)
from gr.animation import animate, save

from _scenarios import SEMINAR_MODEL, run_all

GIF = "--gif" in sys.argv

# Shared y-limits for the stable (video04) and runaway (video05) aneurysm videos
# so their panels are on ONE comparable scale.  The limits are sized to keep the
# *stable* response clearly readable; the runaway simply climbs off the top of
# each panel -- which is exactly the visual signature of the instability.
ANEURYSM_YLIMS = {
    "insult": (-0.03, 1.05),   # elastin fraction (1 -> 0.30 stable / 0.03 runaway)
    "stress_k": (0.9, 2.2),    # stable peaks ~1.4; runaway elastin runs to ~7
    "mass_k": (0.0, 1.3),      # stable peaks ~0.55; runaway collagen/smc run to ~2.3
    "radius": (0.97, 1.3),     # stable a/a_0 -> 1.09; runaway -> 2.14
    "thickness": (0.72, 1.3),  # stable h/h_0 dips to 0.82; runaway -> 2.13
}


def _save(anim, name):
    print("  wrote", save(anim, f"docs/videos/{name}", gif=GIF))


def video_kinematic():
    """Twin of fig01 — kinematic growth adapting to hypertension (artery)."""
    art = artery(SEMINAR_MODEL)
    r = kinematic_growth.simulate(art, HYPERTENSION, t_end=1000)
    fig, anim = animate([r], HYPERTENSION, art, quantities=("sigma_norm", "mass", "radius", "thickness"),
                        title="Kinematic growth — hypertension")
    _save(anim, "video01_kinematic_growth")


def video_cmm_turnover():
    """Twin of fig02 — full CMM turnover under hypertension (per constituent)."""
    art = artery(SEMINAR_MODEL)
    r = constrained_mixture.simulate(art, HYPERTENSION, t_end=1200, dt=2.0)
    fig, anim = animate([r], HYPERTENSION, art, quantities=("stress_k", "mass_k", "radius", "thickness"),
                        title="Full constrained mixture — turnover under hypertension")
    _save(anim, "video02_constrained_mixture")


def video_compare_hypertension():
    """Twin of fig03 (top) — all theories under hypertension."""
    art = artery(SEMINAR_MODEL)
    results, eq = run_all(art, HYPERTENSION, t_end=1000)
    fig, anim = animate(results, HYPERTENSION, art, quantities=("mass", "radius", "thickness"),
                        equilibrium=eq, title="Hypertension — four theories")
    _save(anim, "video03_compare_hypertension")


def video_compare_aneurysm():
    """Twin of fig03 (bottom) — a mild aneurysm (elastin 30%).

    Kinematic growth is DROPPED here: it is a single material, so an elastin-loss
    insult is not meaningful for it.  Only the constrained-mixture theories.
    """
    art = artery(SEMINAR_MODEL)
    results, eq = run_all(art, ANEURYSM, t_end=5000, cmm_dt=2.0)
    results = [r for r in results if r.theory != "kinematic growth"]
    fig, anim = animate(results, ANEURYSM, art, quantities=("mass", "radius", "thickness"),
                        equilibrium=eq, title="Aneurysm (elastin → 30%) — constrained mixtures")
    _save(anim, "video03_compare_aneurysm")


def video_stable_aneurysm():
    """Full CMM, mild aneurysm (elastin 30%) — a STABLE adaptation (has an equilibrium)."""
    art = artery(SEMINAR_MODEL)
    r = constrained_mixture.simulate(art, ANEURYSM, t_end=4000, dt=2.0)
    fig, anim = animate([r], ANEURYSM, art, quantities=("stress_k", "mass_k", "radius", "thickness"),
                        ylims=ANEURYSM_YLIMS,
                        title="Stable aneurysm — full CMM (elastin → 30%)")
    _save(anim, "video04_stable_aneurysm")


def video_runaway():
    """Full CMM, severe elastin loss (3%) — an UNSTABLE runaway (no equilibrium)."""
    art = artery(SEMINAR_MODEL)
    severe = Insult(elastin_surviving=0.03, t_on=1.0, ramp=10.0)
    r = constrained_mixture.simulate(art, severe, t_end=8000, dt=3.0)
    fig, anim = animate([r], severe, art, quantities=("stress_k", "mass_k", "radius", "thickness"),
                        ylims=ANEURYSM_YLIMS,
                        title="Runaway aneurysm — full CMM (elastin → 3%, no equilibrium)")
    _save(anim, "video05_runaway_aneurysm")


VIDEOS = [
    video_kinematic,
    video_cmm_turnover,
    video_compare_hypertension,
    video_compare_aneurysm,
    video_stable_aneurysm,
    video_runaway,
]


def main():
    for build in VIDEOS:
        print(f"--- {build.__name__} ---")
        build()
    print("\nAll videos written to docs/videos/.")


if __name__ == "__main__":
    main()

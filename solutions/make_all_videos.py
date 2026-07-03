"""
TEACHER video generator — an animated twin of each simulation figure.

Every video is built from the SAME simulation results as the corresponding
static figure (via ``gr.animation``), so the numbers always match.  Each shows a
deforming vessel tinted by stress, the insult over time (so the immediate elastic
jump is separated from the slow G&R), and the response curves drawn live.

Run:  uv run python solutions/make_all_videos.py
      uv run python solutions/make_all_videos.py --gif      # GIFs for inline docs

Output: docs/videos/*.mp4  (or *.gif with --gif)

Non-time figures (fig00 setup, fig01 constitutive, and the parameter-sweep panels
of fig05/fig06) have no "live" analogue and are intentionally left as figures.
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


def _save(anim, name):
    print("  wrote", save(anim, f"docs/videos/{name}", gif=GIF))


def video_kinematic():
    """Twin of fig02 — kinematic growth adapting to hypertension (artery)."""
    art = artery(SEMINAR_MODEL)
    r = kinematic_growth.simulate(art, HYPERTENSION, t_end=1000)
    fig, anim = animate([r], HYPERTENSION, art, quantities=("stress_k", "mass", "radius"),
                        title="Kinematic growth — hypertension")
    _save(anim, "video02_kinematic_growth")


def video_cmm_turnover():
    """Twin of fig03 — full CMM turnover under hypertension (per constituent)."""
    art = artery(SEMINAR_MODEL)
    r = constrained_mixture.simulate(art, HYPERTENSION, t_end=1200, dt=2.0)
    fig, anim = animate([r], HYPERTENSION, art, quantities=("stress_k", "mass_k", "radius"),
                        title="Full constrained mixture — turnover under hypertension")
    _save(anim, "video03_constrained_mixture")


def video_compare_hypertension():
    """Twin of fig04 (top) — all theories under hypertension."""
    art = artery(SEMINAR_MODEL)
    results, eq = run_all(art, HYPERTENSION, t_end=1000)
    fig, anim = animate(results, HYPERTENSION, art, quantities=("mass", "radius", "thickness"),
                        equilibrium=eq, title="Hypertension — four theories")
    _save(anim, "video04_compare_hypertension")


def video_compare_aneurysm():
    """Twin of fig04 (bottom) — all theories under a mild aneurysm (elastin 30%)."""
    art = artery(SEMINAR_MODEL)
    results, eq = run_all(art, ANEURYSM, t_end=5000, cmm_dt=2.0)
    fig, anim = animate(results, ANEURYSM, art, quantities=("mass", "radius", "thickness"),
                        equilibrium=eq, title="Aneurysm (elastin → 30%) — four theories")
    _save(anim, "video04_compare_aneurysm")


def video_runaway():
    """Twin of fig06 (unstable trace) — severe elastin loss with no equilibrium."""
    art = artery(SEMINAR_MODEL)
    severe = Insult(elastin_surviving=0.03, t_on=1.0, ramp=10.0)
    r = homogenized_cmm.simulate(art, severe, t_end=5000)
    fig, anim = animate([r], severe, art, quantities=("stress_k", "mass_k", "radius"),
                        title="Runaway aneurysm (elastin → 3%, no equilibrium)")
    _save(anim, "video06_runaway_aneurysm")


VIDEOS = [
    video_kinematic,
    video_cmm_turnover,
    video_compare_hypertension,
    video_compare_aneurysm,
    video_runaway,
]


def main():
    for build in VIDEOS:
        print(f"--- {build.__name__} ---")
        build()
    print("\nAll videos written to docs/videos/.")


if __name__ == "__main__":
    main()

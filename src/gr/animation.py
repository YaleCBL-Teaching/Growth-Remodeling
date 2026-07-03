r"""
Live animations of the G&R simulations — every simulation figure has a video twin.

Nothing here re-implements any physics: an animation is built *entirely* from the
:class:`~gr.history.Result` objects the models already return (plus the
:class:`~gr.parameters.Insult` and the :class:`~gr.geometry.Geometry`).  So a video
always shows exactly the same numbers as the corresponding figure.

The timeline is split into three clearly labelled phases so you can tell apart what
is *reference*, what is *elastic*, and what is *G&R*:

  1. **Reference** — the homeostatic state (no insult).
  2. **Elastic** — the insult is applied with G&R switched OFF: an instantaneous
     mechanical (elastic) response, computed by mechanical equilibrium at the new
     load with the reference mass.  This happens at "negative time", before G&R.
  3. **G&R** — growth & remodeling is switched on (t >= 0) and the tissue slowly
     adapts.  Frames are dense early (where the action is) and the time axis is
     cropped to the active window, so the video does not sit on a flat tail.

Each frame shows a deforming vessel (white lumen, Stanford-red wall, thick lines)
with a dashed **reference** outline and a live "% vs reference" readout so the
change is always visible; single-theory videos plot the **per-constituent** stress
sigma^k/sigma_h^k (each constituent has its own homeostatic stress) and mass, while
comparison videos plot the geometry (mid-wall radius, wall thickness, mass) across
theories.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle, Rectangle

from .history import Result
from .parameters import Insult
from .plotting import STYLE, _repo_root, plt

STANFORD_RED = "#8C1515"
_WALL_EXAGG = 3.0          # wall drawn this much thicker than scale, so it's visible

# Capitalised, descriptive y-axis labels (no plot titles — the label is enough).
# Single-valued quantities (one line per theory):
QUANTITIES = {
    "mass": (r"Mass ratio  $M/M_0$", lambda r: r.mass),
    "lam": (r"Stretch  $\lambda$", lambda r: r.lam),
    "radius": ("Mid-wall radius  [mm]", lambda r: r.radius),
    "thickness": ("Wall thickness  [mm]", lambda r: r.thickness),
}
# Per-constituent quantities (one line per constituent, single theory). Each has
# its OWN homeostatic set-point, so the stress is normalised by sigma_h^k.
PER_CONSTITUENT = {
    "stress_k": (r"Constituent stress  $\sigma^k/\sigma_h^k$", "stresses"),
    "mass_k": (r"Constituent mass  $M^k/M_0$", "masses"),
}


def _finite(t, y):
    ok = np.isfinite(t) & np.isfinite(y)
    if not ok.any():
        return np.array([0.0]), np.array([np.nan])
    return t[ok], y[ok]


def _settle_time(results, t_end: float) -> float:
    """Time by which the response has essentially adapted (for cropping the axis)."""
    ts = 0.0
    for r in results:
        if r.diverged:
            return t_end
        for arr in (r.mass, r.lam):
            t, y = _finite(r.t, arr)
            final = y[-1]
            off = np.abs(y - final) > 0.03 * max(abs(final), 1e-9)
            if off.any():
                ts = max(ts, t[np.where(off)[0][-1]])
    return float(min(t_end, 1.2 * ts + 15.0))


def _elastic_state(geom, insult: Insult):
    """Instantaneous elastic response to the full insult (G&R off, reference mass).

    Theory-independent: at the elastic instant every constituent's stretch is
    G^k * lambda (reference natural configs), so this is one mechanical solve.
    """
    model = geom.model
    s = insult.elastin_surviving

    def supplied(lam):
        tot = 0.0
        for c in model.constituents:
            phi = c.phi0 * (s if c.name == "elastin" else 1.0)
            tot += phi * c.law.stress_cauchy(c.G * lam)
        return tot

    # elastin loss removes mass immediately, so the total mass (hence the wall
    # thickness carrying the load) drops before any G&R.
    m_e = sum(c.phi0 * (s if c.name == "elastin" else 1.0) for c in model.constituents)
    lam = geom.equilibrium_stretch(supplied, mass_ratio=m_e, load_factor=insult.pressure_factor)
    if lam is None:
        return 1.0, 1.0, 1.0
    return lam, supplied(lam) / model.sigma_bar_h, m_e


def animate(
    results: list[Result],
    insult: Insult,
    geom,
    *,
    quantities: tuple[str, ...] = ("stress_k", "mass_k"),
    vessel_from: Result | None = None,
    equilibrium=None,
    n_frames: int = 150,
    title: str | None = None,
):
    """Reference -> Elastic -> G&R animation (vessel + insult + response).

    ``quantities`` may mix single-valued keys from ``QUANTITIES`` (one line per
    theory) and per-constituent keys from ``PER_CONSTITUENT`` (one line per
    constituent; single theory only).
    """
    model = geom.model
    R0, H0 = model.R, model.H
    cons = model.constituents
    s = insult.elastin_surviving
    if vessel_from is None:
        vessel_from = next((r for r in results if r.theory == "full CMM"), results[-1])

    t_end = max(float(r.t[np.isfinite(r.t)][-1]) for r in results)
    t0 = insult.t_on + max(insult.ramp, 0.0)           # insult fully applied ~ elastic instant
    settle = _settle_time(results, t_end)
    t_vis = max(settle - t0, 0.15 * settle, 30.0)      # G&R window shown (days since insult)
    W = 0.20 * t_vis

    lam_e, sig_e, m_e = _elastic_state(geom, insult)

    # --- frame clock: [reference | elastic] in negative time, then G&R --------
    n_ref, n_el = 6, 9
    setup_t = np.concatenate([np.linspace(-W, -0.52 * W, n_ref),
                              np.linspace(-0.5 * W, -1e-4, n_el)])
    gr_t = t_vis * np.linspace(0.0, 1.0, n_frames) ** 1.7
    end_t = np.full(4, t_vis)
    frame_t = np.concatenate([setup_t, gr_t, end_t])
    gr_all = np.concatenate([gr_t, end_t])

    def build(ref_v, ela_v, t, y):
        gr = np.interp(gr_all + t0, t, y, left=y[0], right=y[-1])
        return np.concatenate([np.full(n_ref, ref_v), np.full(n_el, ela_v), gr])

    # single-valued reference/elastic values (elastin loss drops the mass)
    REF = {"mass": 1.0, "lam": 1.0, "radius": R0, "thickness": H0}
    ELA = {"mass": m_e, "lam": lam_e, "radius": lam_e * R0,
           "thickness": geom.thickness(lam_e, m_e)}

    def build_regular(result, q):
        t, y = _finite(result.t, QUANTITIES[q][1](result))
        return build(REF[q], ELA[q], t, y)

    def pc_ref_ela(qk, name):
        c = model.by_name(name)
        if qk == "stress_k":                            # sigma^k/sigma_h^k
            return 1.0, c.law.stress_cauchy(c.G * lam_e) / c.sigma_h
        return c.phi0, c.phi0 * (s if name == "elastin" else 1.0)   # mass_k

    def build_pc(result, qk, name):
        arr = getattr(result, PER_CONSTITUENT[qk][1])[name]
        t, y = _finite(result.t, arr)
        ref, ela = pc_ref_ela(qk, name)
        return build(ref, ela, t, y)

    # vessel geometry over the whole clock (mid-wall radius, thickness, mass)
    a_v = build(R0, lam_e * R0, *_finite(vessel_from.t, vessel_from.radius))
    h_v = build(H0, geom.thickness(lam_e, m_e), *_finite(vessel_from.t, vessel_from.thickness))
    m_v = build(1.0, m_e, *_finite(vessel_from.t, vessel_from.mass))

    # insult drivers (step at the start of the elastic phase)
    applied = np.arange(len(frame_t)) >= n_ref
    gamma = np.where(applied, insult.pressure_factor, 1.0)
    ela_frac = np.where(applied, insult.elastin_surviving, 1.0)
    has_p = insult.pressure_factor != 1.0
    has_e = insult.elastin_surviving != 1.0

    # --------------------------------------------------------------- layout
    ncol = 1 + len(quantities)
    fig = plt.figure(figsize=(3.8 * ncol, 5.2))
    gs = fig.add_gridspec(2, ncol, height_ratios=[2.4, 1.0], hspace=0.55, wspace=0.4)
    ax_v = fig.add_subplot(gs[0, 0]); ax_v.set_aspect("equal"); ax_v.axis("off")
    ax_ins = fig.add_subplot(gs[1, 0])
    ax_q = [fig.add_subplot(gs[:, 1 + i]) for i in range(len(quantities))]
    time_axes = [ax_ins, *ax_q]
    is_artery = results[0].setting == "artery"

    # vessel: RED wall, WHITE lumen (mid-wall radius +/- thickness), with a clearly
    # visible dashed REFERENCE outline on top so the change is always obvious.
    EX = 4.0                                            # wall-thickness exaggeration
    def _disc(radius, **kw):
        p = Circle((0, 0), radius, **kw); ax_v.add_patch(p); return p

    if is_artery:
        inner0, outer0 = (a_v[0] - EX * h_v[0] / 2) / R0, (a_v[0] + EX * h_v[0] / 2) / R0
        lim = 1.15 * np.nanmax((a_v + EX * h_v / 2) / R0)
        ax_v.set_xlim(-lim, lim); ax_v.set_ylim(-lim, lim)
        wall = _disc(outer0, facecolor=STANFORD_RED, edgecolor="#111", lw=2.5, zorder=2)
        lumen = _disc(inner0, facecolor="white", edgecolor="#111", lw=2.5, zorder=3)
        ir, orf = 1.0 - EX * H0 / (2 * R0), 1.0 + EX * H0 / (2 * R0)
        _disc(orf, facecolor="none", edgecolor="#16405e", ls=(0, (5, 3)), lw=1.8, zorder=5)
        _disc(ir, facecolor="none", edgecolor="#16405e", ls=(0, (5, 3)), lw=1.8, zorder=5)
    else:
        ax_v.set_xlim(-0.15, 2.8); ax_v.set_ylim(-1.2, 1.2)
        ax_v.add_patch(Rectangle((0, -0.25), 1.8, 0.5, facecolor="none",
                                 edgecolor="#16405e", ls=(0, (5, 3)), lw=1.8, zorder=5))
        wall = Rectangle((0, -0.25), 1.8, 0.5, facecolor=STANFORD_RED, edgecolor="#111", lw=2.5)
        ax_v.add_patch(wall); lumen = None

    ax_v.set_title(r"artery cross-section  (— — reference)" if is_artery else "bar",
                   fontsize=10)
    phase_txt = ax_v.text(0.5, -0.02, "", transform=ax_v.transAxes, ha="center",
                          va="top", fontsize=12, color="#222", weight="bold")
    readout = ax_v.text(0.5, -0.16, "", transform=ax_v.transAxes, ha="center",
                        va="top", fontsize=9.5, color="#16405e")

    # insult panel: no legend — the ratio goes into the y-label
    if has_p and not has_e:
        ax_ins.plot(frame_t, gamma, color="#2a6fb0", lw=2)
        ax_ins.set_ylabel(r"Pressure  $P/P_h$")
    elif has_e and not has_p:
        ax_ins.plot(frame_t, ela_frac, color=STANFORD_RED, lw=2)
        ax_ins.set_ylabel("Elastin fraction")
    else:
        if has_p:
            ax_ins.plot(frame_t, gamma, color="#2a6fb0", lw=2)
        if has_e:
            ax_ins.plot(frame_t, ela_frac, color=STANFORD_RED, lw=2)
        ax_ins.set_ylabel(r"Insult ($P/P_h$, elastin)")

    # region shading (reference vs elastic) + G&R-on divider
    for ax in time_axes:
        ax.set_xlim(-W, t_vis)
        ax.axvspan(-W, -0.5 * W, color="0.93", zorder=0)
        ax.axvspan(-0.5 * W, 0.0, color="0.85", zorder=0)
        ax.axvline(0.0, color="gray", lw=1.2, ls="--")
        ax.set_xlabel("Time  [day]")
    ax_q[0].annotate("reference", (-0.75 * W, 0.5), xycoords=("data", "axes fraction"),
                     ha="center", va="center", rotation=90, fontsize=8, color="#666")
    ax_q[0].annotate("elastic", (-0.25 * W, 0.5), xycoords=("data", "axes fraction"),
                     ha="center", va="center", rotation=90, fontsize=8, color="#666")

    # response panels
    lines = {}
    for ax, q in zip(ax_q, quantities):
        lines[q] = []
        if q in PER_CONSTITUENT:
            r0 = results[0]
            store = getattr(r0, PER_CONSTITUENT[q][1])
            names = [c.name for c in cons if c.name in store]
            for name in names:
                y = build_pc(r0, q, name)
                ax.plot(frame_t, y, color="gray", lw=0.8, alpha=0.18)
                ln, = ax.plot([], [], lw=2.4, label=name)
                lines[q].append((ln, y))
            if q == "stress_k":                          # shared homeostatic set-point
                ax.axhline(1.0, color="gray", lw=1, ls=":", alpha=0.8)
            ax.set_ylabel(PER_CONSTITUENT[q][0])
        else:
            for r in results:
                y = build_regular(r, q)
                ax.plot(frame_t, y, color="gray", lw=0.8, alpha=0.16)
                ln, = ax.plot([], [], label=r.theory, **STYLE.get(r.theory, {}))
                lines[q].append((ln, y))
            ax.axhline(REF[q], color="gray", lw=1, ls=":", alpha=0.8)
            if equilibrium is not None and getattr(equilibrium, "exists", False):
                val = {"mass": equilibrium.mass, "lam": equilibrium.lam,
                       "radius": equilibrium.radius, "thickness": equilibrium.thickness}.get(q)
                if val is not None and np.isfinite(val):
                    ax.axhline(val, **STYLE["equilibrated CMM"], alpha=0.9,
                               label="equilibrated CMM")
            ax.set_ylabel(QUANTITIES[q][0])
        ax.axvline(frame_t[0], color="k", lw=1, alpha=0.6)  # placeholder cursor added below

    cursors = [ax.axvline(frame_t[0], color="k", lw=1, alpha=0.6) for ax in ax_q]

    # one shared legend, OUTSIDE the axes (constituents if per-constituent, else theories)
    if any(q in PER_CONSTITUENT for q in quantities):
        pcq = next(q for q in quantities if q in PER_CONSTITUENT)
        handles = [ln for ln, _ in lines[pcq]]
        labels = [h.get_label() for h in handles]
    else:
        handles, labels = [], []
        for ax in ax_q:
            for h, lb in zip(*ax.get_legend_handles_labels()):
                if lb and not lb.startswith("_") and lb not in labels:
                    handles.append(h); labels.append(lb)

    if title:
        fig.suptitle(title, fontsize=14, y=0.985)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fig.tight_layout(rect=(0, 0, 1, 0.86))
    if len(labels) >= 2:
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.93),
                   ncol=min(len(labels), 4), fontsize=9, frameon=False)

    # --------------------------------------------------------------- frames
    def phase_label(k):
        if k < n_ref:
            return "reference"
        if k < n_ref + n_el:
            return "insult applied\n(elastic response)"
        if vessel_from.diverged and k >= len(frame_t) - 6:
            return "G&R  →  runaway"
        return "G&R"

    def update(k):
        t = frame_t[k]
        for q in quantities:
            for ln, ys in lines[q]:
                ln.set_data(frame_t[: k + 1], ys[: k + 1])
        for c in cursors:
            c.set_xdata([t, t])
        if is_artery:
            inner = (a_v[k] - EX * h_v[k] / 2) / R0
            outer = (a_v[k] + EX * h_v[k] / 2) / R0
            wall.set_radius(outer); lumen.set_radius(max(inner, 1e-3))
        else:
            wall.set_width(1.8 * a_v[k] / R0)
            ht = 0.5 * h_v[k] / H0
            wall.set_height(ht); wall.set_xy((0, -ht / 2))
        readout.set_text(
            f"vs reference:  radius {a_v[k]/R0-1:+.0%},  "
            f"thickness {h_v[k]/H0-1:+.0%},  mass {m_v[k]-1:+.0%}"
        )
        phase_txt.set_text(phase_label(k))
        return []

    anim = FuncAnimation(fig, update, frames=len(frame_t), interval=70, blit=False)
    return fig, anim


def save(anim, filename: str | Path, *, fps: int = 14, gif: bool = False, dpi: int = 110) -> Path:
    """Write an animation to ``docs/videos/`` as MP4 (default) or GIF.

    A relative ``filename`` is resolved against the repository root.  MP4 uses the
    bundled ffmpeg (via ``imageio-ffmpeg`` if a system ffmpeg is absent); if no
    MP4 writer is available it falls back to an animated GIF.
    """
    path = Path(filename)
    if not path.is_absolute():
        path = _repo_root() / path
    path.parent.mkdir(parents=True, exist_ok=True)

    from matplotlib.animation import writers

    try:
        import imageio_ffmpeg
        import matplotlib
        matplotlib.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    if not gif and writers.is_available("ffmpeg"):
        path = path.with_suffix(".mp4")
        anim.save(str(path), writer="ffmpeg", fps=fps, dpi=dpi)
    else:
        path = path.with_suffix(".gif")
        anim.save(str(path), writer="pillow", fps=fps, dpi=max(dpi - 30, 70))
    plt.close(anim._fig)
    return path

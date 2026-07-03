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

Each frame shows a deforming vessel (Stanford-red lumen, thick walls) with a dashed
**reference** outline so the change from reference is always visible, the insult
drawn over time, and the response curves revealed live.
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
# "Mixture stress" makes clear it is the mixture (not a single constituent).
QUANTITIES = {
    "sigma_norm": (r"Mixture stress  $\bar\sigma/\bar\sigma_h$", lambda r: r.sigma_norm),
    "mass": (r"Mass ratio  $M/M_0$", lambda r: r.mass),
    "lam": (r"Stretch  $\lambda$", lambda r: r.lam),
    "radius": ("Inner radius  [mm]", lambda r: r.radius),
    "thickness": ("Wall thickness  [mm]", lambda r: r.thickness),
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
    quantities: tuple[str, ...] = ("sigma_norm", "mass"),
    vessel_from: Result | None = None,
    per_constituent: bool = False,
    equilibrium=None,
    n_frames: int = 150,
    title: str | None = None,
):
    """Build a Reference -> Elastic -> G&R animation (vessel + insult + response)."""
    model = geom.model
    R0, H0 = model.R, model.H
    t_end = max(float(r.t[np.isfinite(r.t)][-1]) for r in results)
    # The G&R curves start at t0 (insult fully applied ~ the elastic instant), so
    # they begin from the elastic state instead of dipping back to the reference
    # baseline right before G&R switches on.
    t0 = insult.t_on + max(insult.ramp, 0.0)
    settle = _settle_time(results, t_end)
    t_vis = max(settle - t0, 0.15 * settle, 30.0)      # G&R window shown (days since insult)
    W = 0.20 * t_vis                                   # width of the reference+elastic setup

    if vessel_from is None:
        vessel_from = next((r for r in results if r.theory == "full CMM"), results[-1])

    lam_e, sig_e, m_e = _elastic_state(geom, insult)
    # reference and elastic value of each quantity (elastin loss drops the mass)
    REF = {"sigma_norm": 1.0, "mass": 1.0, "lam": 1.0, "radius": R0, "thickness": H0}
    ELA = {"sigma_norm": sig_e, "mass": m_e, "lam": lam_e,
           "radius": lam_e * R0, "thickness": geom.thickness(lam_e, m_e)}

    # --- frame clock: [reference | elastic] in negative time, then G&R ------------
    n_ref, n_el = 6, 9
    setup_t = np.concatenate([np.linspace(-W, -0.52 * W, n_ref),
                              np.linspace(-0.5 * W, -1e-4, n_el)])
    gr_t = t_vis * np.linspace(0.0, 1.0, n_frames) ** 1.7      # dense early
    end_t = np.full(4, t_vis)
    frame_t = np.concatenate([setup_t, gr_t, end_t])
    gr_all = np.concatenate([gr_t, end_t])

    def build(result, getter, key):
        t, y = _finite(result.t, getter(result))
        gr = np.interp(gr_all + t0, t, y, left=y[0], right=y[-1])
        return np.concatenate([np.full(n_ref, REF[key]), np.full(n_el, ELA[key]), gr])

    series = {q: [build(r, QUANTITIES[q][1], q) for r in results] for q in quantities}
    r_v = build(vessel_from, lambda r: r.radius, "radius")
    h_v = build(vessel_from, lambda r: r.thickness, "thickness")

    # insult drivers step at the start of the elastic phase (t = -0.5 W)
    applied = np.arange(len(frame_t)) >= n_ref
    gamma = np.where(applied, insult.pressure_factor, 1.0)
    ela_frac = np.where(applied, insult.elastin_surviving, 1.0)
    has_p = insult.pressure_factor != 1.0
    has_e = insult.elastin_surviving != 1.0

    # ---------------------------------------------------------------- layout
    ncol = 1 + len(quantities)
    fig = plt.figure(figsize=(3.8 * ncol, 5.0))
    gs = fig.add_gridspec(2, ncol, height_ratios=[2.4, 1.0], hspace=0.5, wspace=0.36)
    ax_v = fig.add_subplot(gs[0, 0]); ax_v.set_aspect("equal"); ax_v.axis("off")
    ax_ins = fig.add_subplot(gs[1, 0])
    ax_q = [fig.add_subplot(gs[:, 1 + i]) for i in range(len(quantities))]
    time_axes = [ax_ins, *ax_q]

    is_artery = results[0].setting == "artery"

    # vessel: dashed reference ghost + current (Stanford-red lumen, thick walls)
    def _disc(radius, **kw):
        p = Circle((0, 0), radius, **kw); ax_v.add_patch(p); return p

    if is_artery:
        out_ref = 1.0 + _WALL_EXAGG * H0 / R0
        max_out = np.nanmax(r_v / R0 + _WALL_EXAGG * h_v / R0)
        lim = 1.18 * max_out
        ax_v.set_xlim(-lim, lim); ax_v.set_ylim(-lim, lim)
        # dotted reference outline in the background; wall RED, lumen WHITE
        _disc(out_ref, facecolor="none", edgecolor="gray", ls=":", lw=1.4, zorder=1)
        _disc(1.0, facecolor="none", edgecolor="gray", ls=":", lw=1.4, zorder=1)
        wall = _disc(out_ref, facecolor=STANFORD_RED, edgecolor="#111", lw=3.0, zorder=2)
        lumen = _disc(1.0, facecolor="white", edgecolor="#111", lw=3.0, zorder=3)
    else:
        ax_v.set_xlim(-0.15, 2.8); ax_v.set_ylim(-1.2, 1.2)
        h_ref = 0.5
        ax_v.add_patch(Rectangle((0, -h_ref / 2), 1.8, h_ref, facecolor="none",
                                 edgecolor="gray", ls=":", lw=1.4))
        wall = Rectangle((0, -h_ref / 2), 1.8, h_ref, facecolor=STANFORD_RED,
                         edgecolor="#111", lw=3.0)
        ax_v.add_patch(wall); lumen = None
    phase_txt = ax_v.text(0.5, -0.04, "", transform=ax_v.transAxes, ha="center",
                          va="top", fontsize=12, color="#222", weight="bold")

    # insult panel: no legend — the ratio goes straight into the y-label
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

    # region shading (two-tone: reference vs elastic) + G&R-on divider
    for ax in time_axes:
        ax.set_xlim(-W, t_vis)
        ax.axvspan(-W, -0.5 * W, color="0.93", zorder=0)       # reference
        ax.axvspan(-0.5 * W, 0.0, color="0.85", zorder=0)      # elastic
        ax.axvline(0.0, color="gray", lw=1.2, ls="--")         # G&R switched on
        ax.set_xlabel("Time  [day]")
    # region labels: "reference"/"elastic" set vertically inside their (narrow)
    # bands so they never collide (the G&R region is marked by the t=0 divider and
    # the bold phase caption under the vessel)
    ax_q[0].annotate("reference", (-0.75 * W, 0.5), xycoords=("data", "axes fraction"),
                     ha="center", va="center", rotation=90, fontsize=8, color="#666")
    ax_q[0].annotate("elastic", (-0.25 * W, 0.5), xycoords=("data", "axes fraction"),
                     ha="center", va="center", rotation=90, fontsize=8, color="#666")

    # response panels
    lines, cursors = {}, []
    for ax, q in zip(ax_q, quantities):
        ylabel, _ = QUANTITIES[q]
        lines[q] = []
        if per_constituent and q == "mass" and len(results) == 1:
            r0 = results[0]
            for name, m in r0.masses.items():
                # constituent curve: reference & elastic = phi0, then G&R = mass history
                phi0 = model.by_name(name).phi0
                t, yy = _finite(r0.t, m)
                grc = np.interp(gr_all + t0, t, yy, left=yy[0], right=yy[-1])
                y = np.concatenate([np.full(n_ref, phi0), np.full(n_el, phi0), grc])
                ax.plot(frame_t, y, color="gray", lw=0.8, alpha=0.2)
                ln, = ax.plot([], [], lw=2.4, label=name)
                lines[q].append((ln, y))
        else:
            for r, ys in zip(results, series[q]):
                ax.plot(frame_t, ys, color="gray", lw=0.8, alpha=0.16)
                ln, = ax.plot([], [], label=r.theory, **STYLE.get(r.theory, {}))
                lines[q].append((ln, ys))
        # reference configuration, kept dotted in the background
        ax.axhline(REF[q], color="gray", lw=1, ls=":", alpha=0.7, zorder=0)
        if equilibrium is not None and getattr(equilibrium, "exists", False):
            val = {"sigma_norm": equilibrium.sigma_norm, "mass": equilibrium.mass,
                   "lam": equilibrium.lam, "radius": equilibrium.radius,
                   "thickness": equilibrium.thickness}.get(q)
            if val is not None and np.isfinite(val):
                ax.axhline(val, **STYLE["equilibrated CMM"], alpha=0.9, label="equilibrated CMM")
        ax.set_ylabel(ylabel)
        cursors.append(ax.axvline(frame_t[0], color="k", lw=1, alpha=0.6))

    # one shared legend for the response panels, placed OUTSIDE the axes so it is
    # fixed (never moves or overlaps the growing curves)
    if per_constituent:
        handles = [ln for ln, _ in lines.get("mass", [])]
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

    # ---------------------------------------------------------------- frames
    def phase_label(k):
        if k < n_ref:
            return "Reference"
        if k < n_ref + n_el:
            return "Insult applied\n(elastic response)"
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
        rr, hh = r_v[k] / R0, _WALL_EXAGG * h_v[k] / R0
        if is_artery:
            wall.set_radius(rr + hh)
            lumen.set_radius(rr)
        else:
            wall.set_width(1.8 * rr)
            ht = 0.5 * h_v[k] / H0
            wall.set_height(ht); wall.set_xy((0, -ht / 2))
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

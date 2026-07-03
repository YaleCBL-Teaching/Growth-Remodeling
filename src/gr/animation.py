r"""
Live animations of the G&R simulations — every simulation figure has a video twin.

Nothing here re-implements any physics: an animation is built *entirely* from the
:class:`~gr.history.Result` objects the models already return (plus the
:class:`~gr.parameters.Insult` and the :class:`~gr.geometry.Geometry`).  So a video
always shows exactly the same numbers as the corresponding figure.

Layout is a 16:9 grid: a large **vessel** cross-section on the left and a grid of
**live plots** on the right (the insult is one of them, animated like the rest).
The raw simulation is played over its active time window -- frames are dense early
and the flat tail is cropped; there is no separate elastic stage.

The vessel is drawn with a **light-gray current wall** about the mid-wall radius
and a bold **red reference outline** (fixed), so the change from the reference
configuration is easy to see.  Single-theory videos plot the **per-constituent**
stress sigma^k/sigma_h^k (each constituent has its own homeostatic stress) and
mass -- collagen and smooth muscle remodel back to sigma_h^k while elastin cannot;
comparison videos plot the geometry (mid-wall radius, wall thickness) and mass
across theories.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle, Rectangle

from .history import Result
from .parameters import Insult
from .plotting import CONSTITUENT_STYLE, NEUTRAL, STYLE, constituent_order, _repo_root, plt

STANFORD_RED = "#8C1515"

# Capitalised, descriptive y-axis labels (no plot titles — the label is enough).
# Single-valued quantities (one line per theory):
QUANTITIES = {
    "sigma_norm": (r"Wall stress  $\sigma/\sigma_h$", lambda r: r.sigma_norm),  # single material
    "mass": (r"Mass ratio  $M/M_0$", lambda r: r.mass),
    "lam": (r"Stretch  $\lambda$", lambda r: r.lam),
    "radius": (r"Radius ratio  $a/a_0$", lambda r: r.radius),        # normalised in animate()
    "thickness": (r"Thickness ratio  $h/h_0$", lambda r: r.thickness),
}
# reference-normalising factors for the single-valued quantities (a/a_0, h/h_0)
_NORM = {"radius": "R0", "thickness": "H0"}
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



def animate(
    results: list[Result],
    insult: Insult,
    geom,
    *,
    quantities: tuple[str, ...] = ("stress_k", "mass_k"),
    vessel_from: Result | None = None,
    equilibrium=None,
    n_frames: int = 240,
    title: str | None = None,
    ylims: dict[str, tuple[float, float]] | None = None,
):
    """Animation (16:9) of the simulation: a big vessel + a grid of live plots.

    ``quantities`` may mix single-valued keys from ``QUANTITIES`` (one line per
    theory) and per-constituent keys from ``PER_CONSTITUENT`` (one line per
    constituent; single theory only).  The insult is one of the grid panels,
    animated like the rest.  There is no separate elastic stage: the raw
    simulation is played over its active time window.

    ``ylims`` optionally fixes the y-range of individual panels (keyed by the
    quantity name, or ``"insult"`` for the insult panel) instead of autoscaling.
    Passing the SAME ``ylims`` to two videos makes their axes directly
    comparable; a curve that exceeds a panel's range simply runs off the top
    (useful to contrast a stable response against a runaway one on one scale).
    """
    import math

    model = geom.model
    R0, H0 = model.R, model.H
    cons = model.constituents
    if vessel_from is None:
        vessel_from = next((r for r in results if r.theory == "full CMM"), results[-1])

    t_end = max(float(r.t[np.isfinite(r.t)][-1]) for r in results)
    t_vis = min(t_end, 1.6 * _settle_time(results, t_end))     # show a longer window

    # frame clock: a short baseline at slightly negative time (drawn but not
    # labelled) so the change from baseline is visible, then early-dense over the
    # active window.
    t_lo = -0.06 * t_vis
    main = t_vis * np.linspace(0.0, 1.0, n_frames) ** 1.6
    frame_t = np.concatenate([np.linspace(t_lo, 0.0, 5, endpoint=False), main,
                              np.full(3, t_vis)])

    def interp(result, getter):
        t, y = _finite(result.t, getter(result))
        return np.interp(frame_t, t, y, left=y[0], right=y[-1])

    gamma = np.array([insult.pressure(1.0, t) for t in frame_t])
    ela_frac = np.array([insult.elastin_fraction(t) for t in frame_t])
    has_p = insult.pressure_factor != 1.0
    has_e = insult.elastin_surviving != 1.0

    REF = {"sigma_norm": 1.0, "mass": 1.0, "lam": 1.0, "radius": 1.0, "thickness": 1.0}
    norm = {"radius": R0, "thickness": H0}                             # a/a_0, h/h_0
    is_artery = results[0].setting == "artery"

    # --- layout: 16:9, big vessel (2x2) + a grid of time-plots ---------------
    n_time = len(quantities) + 1                       # + the insult panel
    plot_cols = math.ceil(n_time / 2)
    total_cols = 2 + plot_cols
    # Literal 12.8x7.2 in (a 16:9 frame): at the save dpi this must land on an
    # EXACT even integer pixel count.  Writing 16/9*7.2 instead gives
    # 12.79999998, which the ffmpeg writer truncates to an odd 1407 while the Agg
    # canvas rounds to 1408 -- that 1px disagreement shears every scanline.
    fig = plt.figure(figsize=(12.8, 7.2))
    gs = fig.add_gridspec(2, total_cols, hspace=0.42, wspace=0.5)
    ax_v = fig.add_subplot(gs[:, 0:2]); ax_v.set_aspect("equal"); ax_v.axis("off")
    plot_axes = [fig.add_subplot(gs[idx // plot_cols, 2 + idx % plot_cols])
                 for idx in range(n_time)]
    ax_ins, ax_q = plot_axes[0], plot_axes[1:]

    # --- vessel: light-gray current wall, RED reference outline, large -------
    EX = 4.0
    a_v = interp(vessel_from, lambda r: r.radius)
    h_v = interp(vessel_from, lambda r: r.thickness)

    def _disc(radius, **kw):
        p = Circle((0, 0), radius, **kw); ax_v.add_patch(p); return p

    if is_artery:
        outer_arr = (a_v + EX * h_v / 2) / R0
        inner_arr = (a_v - EX * h_v / 2) / R0
        lim = 1.12 * np.nanmax(outer_arr)                    # headroom above the vessel
        ax_v.set_xlim(-lim, lim); ax_v.set_ylim(-lim, lim)
        wall = _disc(outer_arr[0], facecolor="#d9d9d9", edgecolor="#666", lw=1.5, zorder=2)
        lumen = _disc(inner_arr[0], facecolor="white", edgecolor="#666", lw=1.5, zorder=3)
        orf, irf = 1.0 + EX * H0 / (2 * R0), 1.0 - EX * H0 / (2 * R0)
        _disc(orf, facecolor="none", edgecolor=STANFORD_RED, lw=3.0, zorder=5)
        _disc(irf, facecolor="none", edgecolor=STANFORD_RED, lw=3.0, zorder=5)
    else:
        ax_v.set_xlim(-0.15, 2.9); ax_v.set_ylim(-1.3, 1.3)
        ax_v.add_patch(Rectangle((0, -0.3), 1.8, 0.6, facecolor="none",
                                 edgecolor=STANFORD_RED, lw=3.0, zorder=5))
        wall = Rectangle((0, -0.3), 1.8, 0.6, facecolor="#d9d9d9", edgecolor="#666", lw=1.5)
        ax_v.add_patch(wall); lumen = None
    # legend inside the vessel axis (reference vs current); no text UNDER the vessel
    ax_v.plot([], [], color=STANFORD_RED, lw=3, label="reference")
    ax_v.add_patch(Rectangle((0, 0), 0, 0, facecolor="#d9d9d9", edgecolor="#666",
                             label=f"current ({vessel_from.theory})"))
    ax_v.legend(loc="upper center", bbox_to_anchor=(0.5, 1.09), ncol=2,
                fontsize=10, frameon=False)

    # --- helper to add a live curve (faint full guide + revealed line) -------
    lines = {}

    def add_curve(ax, y, **kw):
        ax.plot(frame_t, y, color="gray", lw=0.7, alpha=0.14)
        ln, = ax.plot([], [], **kw)
        return ln

    # insult panel (animated like the rest; ratio in the y-label)
    lines["_insult"] = []
    if has_p:
        lines["_insult"].append((add_curve(ax_ins, gamma, color="black", lw=2.2), gamma))
    if has_e:
        lines["_insult"].append((add_curve(ax_ins, ela_frac, color="black", lw=2.2), ela_frac))
    ax_ins.set_ylabel(r"Pressure  $P/P_h$" if (has_p and not has_e)
                      else ("Elastin fraction" if (has_e and not has_p)
                            else r"Insult ($P/P_h$, elastin)"))
    ax_ins.axhline(1.0, color="gray", lw=1, ls=":", alpha=0.8)
    if ylims and "insult" in ylims:
        ax_ins.set_ylim(*ylims["insult"])

    # quantity panels
    for ax, q in zip(ax_q, quantities):
        lines[q] = []
        if q in PER_CONSTITUENT:
            r0 = results[0]
            store = getattr(r0, PER_CONSTITUENT[q][1])
            for name in constituent_order(c.name for c in cons if c.name in store):
                y = interp(r0, lambda r, n=name, at=PER_CONSTITUENT[q][1]: getattr(r, at)[n])
                lines[q].append((add_curve(ax, y, lw=2.2, label=name,
                                           **CONSTITUENT_STYLE.get(name, {})), y))
            if q == "stress_k":
                ax.axhline(1.0, color="gray", lw=1, ls=":", alpha=0.8)
            ax.set_ylabel(PER_CONSTITUENT[q][0])
        else:
            nf = norm.get(q, 1.0)
            single = len(results) == 1                  # a single theory -> neutral colour
            for r in results:
                kw = dict(color=NEUTRAL, ls="-") if single else STYLE.get(r.theory, {})
                y = interp(r, lambda rr, g=QUANTITIES[q][1], f=nf: g(rr) / f)
                lines[q].append((add_curve(ax, y, label=r.theory, **kw), y))
            ax.axhline(REF[q], color="gray", lw=1, ls=":", alpha=0.8)
            if equilibrium is not None and getattr(equilibrium, "exists", False):
                val = {"sigma_norm": equilibrium.sigma_norm, "mass": equilibrium.mass,
                       "lam": equilibrium.lam, "radius": equilibrium.radius / R0,
                       "thickness": equilibrium.thickness / H0}.get(q)
                if val is not None and np.isfinite(val):
                    ax.axhline(val, **STYLE["equilibrated CMM"], alpha=0.9,
                               label="equilibrated CMM")
            ax.set_ylabel(QUANTITIES[q][0])
        if ylims and q in ylims:
            ax.set_ylim(*ylims[q])

    for ax in plot_axes:
        ax.set_xlim(t_lo, t_vis)
        ax.set_xlabel("Time  [day]")
        ax.set_xticks([tk for tk in ax.get_xticks() if tk >= -1e-9])   # hide negative time
        ax.set_xlim(t_lo, t_vis)
    cursors = [ax.axvline(t_lo, color="k", lw=1, alpha=0.6) for ax in plot_axes]

    # one shared legend for the response panels, outside the axes
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
        fig.suptitle(title, fontsize=15, y=0.985)
    # explicit tight margins so everything sits against the left border
    fig.subplots_adjust(left=0.025, right=0.99, top=0.85, bottom=0.09,
                        wspace=0.5, hspace=0.42)
    ax_v.set_anchor("W")                                     # left-align the square vessel
    # plot legend centred OVER THE PLOTS (right region), lifted clear of the vessel
    if len(labels) >= 2:
        pos = [ax.get_position() for ax in ax_q]
        x_center = 0.5 * (min(p.x0 for p in pos) + max(p.x1 for p in pos))
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(x_center, 0.945),
                   ncol=len(labels), fontsize=8.5, frameon=False,
                   columnspacing=1.1, handlelength=1.6, handletextpad=0.5)

    # --------------------------------------------------------------- frames
    def update(k):
        t = frame_t[k]
        for key in lines:
            for ln, ys in lines[key]:
                ln.set_data(frame_t[: k + 1], ys[: k + 1])
        for c in cursors:
            c.set_xdata([t, t])
        if is_artery:
            wall.set_radius((a_v[k] + EX * h_v[k] / 2) / R0)
            lumen.set_radius(max((a_v[k] - EX * h_v[k] / 2) / R0, 1e-3))
        else:
            wall.set_width(1.8 * a_v[k] / R0)
            ht = 0.6 * h_v[k] / H0
            wall.set_height(ht); wall.set_xy((0, -ht / 2))
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
        # h264/yuv420p requires even width & height; pad up if the figure*dpi is odd.
        anim.save(str(path), writer="ffmpeg", fps=fps, dpi=dpi,
                  extra_args=["-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2"])
    else:
        path = path.with_suffix(".gif")
        anim.save(str(path), writer="pillow", fps=fps, dpi=max(dpi - 30, 70))
    plt.close(anim._fig)
    return path

r"""
Live animations of the G&R simulations — every static figure has a video twin.

Nothing here re-implements any physics: an animation is built *entirely* from the
:class:`~gr.history.Result` objects the models already return (plus the
:class:`~gr.parameters.Insult`, to draw the driver).  So a video always shows
exactly the same numbers as the corresponding figure.

Each animation has three synchronized parts:

  * a **deforming vessel** (or bar) whose radius / wall thickness track the
    simulation, tinted by the current stress relative to homeostatic;
  * the **insult** (pressure factor, surviving elastin) drawn over time, so the
    *immediate elastic* response (the jump when the load steps) is visually
    separated from the *slow growth & remodeling* that follows;
  * the **response** curves, revealed progressively with a moving time cursor.

Use :func:`animate` to build a ``FuncAnimation`` and :func:`save` to write it to
MP4 (for slides) or GIF (for inline docs).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle, Rectangle

from .history import Result
from .parameters import Insult
from .plotting import STYLE, _repo_root, plt

# What each animatable quantity is called and how to pull it from a Result.
QUANTITIES = {
    "sigma_norm": (r"tissue stress  $\bar\sigma/\bar\sigma_h$", lambda r: r.sigma_norm),
    "mass": (r"mass ratio  $M/M_0$", lambda r: r.mass),
    "lam": (r"stretch  $\lambda$", lambda r: r.lam),
    "radius": ("inner radius  [mm]", lambda r: r.radius),
    "thickness": ("wall thickness  [mm]", lambda r: r.thickness),
}

_WALL_EXAGG = 3.0          # wall drawn this much thicker than scale, so it's visible
_STRESS_CMAP = plt.get_cmap("coolwarm")


def _finite(t, y):
    """Truncate a (t, y) series to its leading finite, strictly-increasing part."""
    ok = np.isfinite(t) & np.isfinite(y)
    if not ok.any():
        return np.array([0.0]), np.array([np.nan])
    t, y = t[ok], y[ok]
    return t, y


def _frame_times(t_end: float, insult: Insult, n: int) -> np.ndarray:
    """Frame clock with a clear beat so the fast elastic response is legible:
    hold on homeostasis -> jump -> PAUSE on the elastic response -> slow G&R -> hold.
    """
    t_on, ramp = insult.t_on, max(insult.ramp, 1e-6)
    pre = [0.0] * 4                                    # hold on homeostasis
    jump = [t_on, t_on + 0.5 * ramp]                   # the (fast) elastic response...
    hold_elastic = [t_on + ramp] * 5                   # ...paused so it's visible
    end = [t_end] * 3
    main = np.linspace(t_on + ramp, t_end, max(n - len(pre) - len(jump) - len(hold_elastic) - len(end), 2))
    return np.concatenate([pre, jump, hold_elastic, main, end])


def _stress_color(sig_norm: float):
    return _STRESS_CMAP(np.clip(0.5 + 0.8 * (sig_norm - 1.0), 0.0, 1.0))


def animate(
    results: list[Result],
    insult: Insult,
    *,
    quantities: tuple[str, ...] = ("sigma_norm", "mass"),
    vessel_from: Result | None = None,
    per_constituent: bool = False,
    equilibrium=None,
    n_frames: int = 170,
    title: str | None = None,
):
    """Build a synchronized vessel + insult + response animation.

    Parameters
    ----------
    results : list of Result
        Theories to overlay (all from the same scenario/geometry).
    insult : Insult
        The driver, plotted over time (pressure factor and surviving elastin).
    quantities : which response panels to draw (keys of ``QUANTITIES``).
    vessel_from : which Result drives the vessel (default: full CMM, else the last).
    per_constituent : if True (single result), show its constituent masses instead
        of the overlaid ``mass`` curve.
    """
    setting = results[0].setting
    t_end = max(float(r.t[np.isfinite(r.t)][-1]) for r in results)
    ft = _frame_times(t_end, insult, n_frames)

    if vessel_from is None:
        vessel_from = next((r for r in results if r.theory == "full CMM"), results[-1])

    # --- interpolate everything onto the common frame clock ------------------
    def interp(r: Result, getter):
        t, y = _finite(r.t, getter(r))
        return np.interp(ft, t, y, left=y[0], right=y[-1])

    series = {q: [interp(r, QUANTITIES[q][1]) for r in results] for q in quantities}
    r_v = interp(vessel_from, lambda r: r.radius)
    h_v = interp(vessel_from, lambda r: r.thickness)
    sig_v = interp(vessel_from, lambda r: r.sigma_norm)
    R0, H0 = r_v[0], h_v[0]

    # insult drivers (reuse the Insult; pressure factor is P-independent)
    gamma = np.array([insult.pressure(1.0, t) for t in ft])
    ela = np.array([insult.elastin_fraction(t) for t in ft])
    has_pressure = insult.pressure_factor != 1.0
    has_elastin = insult.elastin_surviving != 1.0

    # ------------------------------------------------------------------ layout
    ncol = 1 + len(quantities)
    fig = plt.figure(figsize=(3.7 * ncol, 5.0))
    gs = fig.add_gridspec(2, ncol, height_ratios=[2.4, 1.0], hspace=0.45, wspace=0.34)
    ax_v = fig.add_subplot(gs[0, 0]); ax_v.set_aspect("equal"); ax_v.axis("off")
    ax_ins = fig.add_subplot(gs[1, 0])
    ax_q = [fig.add_subplot(gs[:, 1 + i]) for i in range(len(quantities))]

    # vessel artists (two discs: wall + lumen) or a bar
    is_artery = setting == "artery"
    max_r = np.nanmax(r_v) + _WALL_EXAGG * np.nanmax(h_v)
    if is_artery:
        lim = 1.25 * max_r / R0
        ax_v.set_xlim(-lim, lim); ax_v.set_ylim(-lim, lim)
        wall = Circle((0, 0), 1.0, facecolor="#c9d6e5", edgecolor="#2b3a4a", lw=1.4, zorder=1)
        lumen = Circle((0, 0), 0.9, facecolor="#eaf3fb", edgecolor="none", zorder=2)
        ax_v.add_patch(wall); ax_v.add_patch(lumen)
    else:
        ax_v.set_xlim(-0.1, 2.6); ax_v.set_ylim(-1.2, 1.2)
        wall = Rectangle((0, -0.3), 1.0, 0.6, facecolor="#c9d6e5", edgecolor="#2b3a4a", lw=1.4)
        lumen = None
        ax_v.add_patch(wall)
    ax_v.set_title(f"{setting}", fontsize=12)
    phase_txt = ax_v.text(0.5, -0.02, "", transform=ax_v.transAxes, ha="center",
                          va="top", fontsize=11, color="#333")

    # insult panel
    if has_pressure:
        ax_ins.plot(ft, gamma, color="#2a6fb0", lw=2, label=r"pressure $P/P_h$")
    if has_elastin:
        ax_ins.plot(ft, ela, color="#c0392b", lw=2, label=r"elastin fraction")
    ax_ins.axhline(1.0, color="gray", lw=0.8, alpha=0.5)
    ax_ins.set_xlim(0, t_end); ax_ins.set_xlabel("time  [day]")
    ax_ins.set_title("insult (the driver)", fontsize=11)
    ax_ins.legend(fontsize=8, loc="best")
    ins_cursor = ax_ins.axvline(0, color="k", lw=1)

    # response panels: full faint guide + revealed bold line + tip + time cursor
    lines, tips, cursors = {}, {}, []
    for ax, q in zip(ax_q, quantities):
        ylabel, _ = QUANTITIES[q]
        if per_constituent and q == "mass" and len(results) == 1:
            r0 = results[0]
            lines[q] = []
            for name, m in r0.masses.items():
                y = np.interp(ft, *_finite(r0.t, m))
                ax.plot(ft, y, color="gray", lw=0.8, alpha=0.25)
                ln, = ax.plot([], [], lw=2.2, label=name)
                lines[q].append((ln, y))
            ax.legend(fontsize=8, loc="best")
        else:
            lines[q] = []
            for r, ys in zip(results, series[q]):
                ax.plot(ft, ys, color="gray", lw=0.8, alpha=0.18)     # faint guide
                ln, = ax.plot([], [], label=r.theory, **STYLE.get(r.theory, {}))
                lines[q].append((ln, ys))
            if q == "sigma_norm":
                ax.axhline(1.0, color="gray", lw=1, alpha=0.5)
            if len(results) > 1:
                ax.legend(fontsize=8, loc="best")
        # equilibrated end-state as a dotted target line
        if equilibrium is not None and getattr(equilibrium, "exists", False):
            val = {"sigma_norm": equilibrium.sigma_norm, "mass": equilibrium.mass,
                   "lam": equilibrium.lam, "radius": equilibrium.radius,
                   "thickness": equilibrium.thickness}.get(q)
            if val is not None and np.isfinite(val):
                ax.axhline(val, **STYLE["equilibrated CMM"], alpha=0.9)
        ax.set_xlim(0, t_end); ax.set_ylabel(ylabel); ax.set_xlabel("time  [day]")
        ax.set_title(q.replace("_", " "), fontsize=11)
        cursors.append(ax.axvline(0, color="k", lw=1, alpha=0.6))

    if title:
        fig.suptitle(title, fontsize=14, y=1.0)
    import warnings
    with warnings.catch_warnings():          # equal-aspect vessel axis is fine here
        warnings.simplefilter("ignore")
        fig.tight_layout()

    # ------------------------------------------------------------------ frames
    t_on, ramp = insult.t_on, max(insult.ramp, 1e-6)

    def phase_label(t, k):
        if t <= t_on:
            return "homeostasis"
        if t <= t_on + ramp + 1e-9:
            return "insult → elastic response"
        if vessel_from.diverged and k >= len(ft) - 4:
            return "unstable → aneurysm"
        return "growth & remodeling"

    def update(k):
        t = ft[k]
        for q in quantities:
            for ln, ys in lines[q]:
                ln.set_data(ft[: k + 1], ys[: k + 1])
        for c in cursors:
            c.set_xdata([t, t])
        ins_cursor.set_xdata([t, t])
        # vessel
        rr, hh = r_v[k] / R0, _WALL_EXAGG * h_v[k] / R0
        if is_artery:
            wall.set_radius(rr + hh)
            lumen.set_radius(rr)
            wall.set_facecolor(_stress_color(sig_v[k]))
        else:
            # bar: length grows with stretch (r/R0 = lambda), height with mass/lambda (h/H0)
            w, ht = 1.8 * r_v[k] / R0, 0.5 * h_v[k] / H0
            wall.set_width(w)
            wall.set_height(ht)
            wall.set_xy((0, -ht / 2))
            wall.set_facecolor(_stress_color(sig_v[k]))
        phase_txt.set_text(phase_label(t, k))
        return []

    anim = FuncAnimation(fig, update, frames=len(ft), interval=60, blit=False)
    return fig, anim


def save(anim, filename: str | Path, *, fps: int = 20, gif: bool = False, dpi: int = 110) -> Path:
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

    # make the pip-bundled ffmpeg discoverable for the MP4 writer
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

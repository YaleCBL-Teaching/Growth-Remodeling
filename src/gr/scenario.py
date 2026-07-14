r"""
Config-driven runner — turn a small YAML **input file** into a finished G&R
experiment, with a one-line **parametric study**.

The whole point of this module is that a student never has to edit Python to run
an exercise or sweep a parameter: they describe *what* to run in a readable
``configs/*.yaml`` file and launch it with ``run.py`` (repository root).  The
same four theories, two geometries and two insults from the rest of the package
are wired up here; nothing new is modelled.

-------------------------------------------------------------------------------
The config schema (all keys optional unless noted)
-------------------------------------------------------------------------------
    title:     free text, used as the plot title
    study:     transient | compare | equilibrium | map      (REQUIRED)
    theory:    kinematic_growth | constrained_mixture | homogenized_cmm
               (REQUIRED for study: transient)
    theories:  [ ... ]   list of the above   (study: compare)

    model:                     # optional overrides of the shared Model
      P_h: 13.3                #   homeostatic pressure [kPa]
      R:   1.0                 #   reference mid-wall radius [mm]
      constituents:            #   per-constituent overrides (by name)
        collagen:
          turnover_days: 20    #   convenience for k_d = 1/turnover_days
          gain: 1.0            #   mechano-sensitivity K_sigma
          G:    1.08           #   deposition stretch
          law:  {c1: 250, c2: 8}   # Fung fiber (or {c: 90} for neo-Hookean)

    insult:                    # the sustained perturbation
      pressure_factor:   1.5   #   hypertension
      elastin_surviving: 1.0   #   aneurysm (fraction of elastin kept)
      t_on: 1.0
      ramp: 1.0

    simulate: {t_end: 1500, k_g: 0.05, dt: 1.0}   # kwargs for .simulate()

    # --- parametric study (study: transient | equilibrium) ---
    sweep:                     # overlay one run per value
      parameter: simulate.k_g  #   dotted path into this config
      values: [0.02, 0.05, 0.2]           # OR  range: {start, stop, num}

    # --- study: equilibrium extras ---
    scan:  {parameter: insult.elastin_surviving, start: 0.6, stop: 0.02, num: 60}
    report_critical: elastin   # also print the critical elastin-loss boundary

    # --- study: map (2-D existence grid) ---
    axes:
      x: {parameter: insult.elastin_surviving, start: 0.6, stop: 0.02, num: 40}
      y: {parameter: insult.pressure_factor,   start: 1.0, stop: 3.0,  num: 40}
"""
from __future__ import annotations

import copy
import inspect
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

from . import (
    constrained_mixture,
    equilibrated_cmm,
    homogenized_cmm,
    kinematic_growth,
)
from .geometry import artery
from .mechanics import FungFiber, NeoHookean
from .monitor import Monitor
from .parameters import Insult, Model
from .stability import adapts, critical_elastin_loss

# name in a config  ->  the module that provides .simulate(geom, insult, ...)
THEORIES = {
    "kinematic_growth": kinematic_growth,
    "constrained_mixture": constrained_mixture,
    "homogenized_cmm": homogenized_cmm,
}


# =============================================================================
# Loading + small config utilities
# =============================================================================
def load_config(path: str | Path) -> dict:
    """Read a YAML config file into a plain dict."""
    import yaml  # local import so the package works without PyYAML until you run one

    with open(path) as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict) or "study" not in cfg:
        raise ValueError(f"{path}: a config needs at least a 'study:' key")
    return cfg


def set_by_path(cfg: dict, dotted: str, value) -> None:
    """Set ``cfg['a']['b'] = value`` from the dotted path ``"a.b"`` (creating dicts)."""
    keys = dotted.split(".")
    d = cfg
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def _axis_values(spec: dict) -> np.ndarray:
    """A list ``values:`` or a ``start/stop/num`` range -> a 1-D array."""
    if "values" in spec:
        return np.asarray(spec["values"], dtype=float)
    return np.linspace(float(spec["start"]), float(spec["stop"]), int(spec["num"]))


def _short(dotted: str) -> str:
    """Last segment of a dotted path, for compact legend labels."""
    return dotted.split(".")[-1]


# =============================================================================
# Build the shared objects from a config
# =============================================================================
def build_model(cfg: dict) -> Model:
    """Construct the shared :class:`Model`, applying any ``model:`` overrides."""
    mc = cfg.get("model") or {}
    model = Model()
    globals_ = {k: float(mc[k]) for k in ("P_h", "R") if k in mc}
    if globals_:
        model = replace(model, **globals_)
    for name, ov in (mc.get("constituents") or {}).items():
        model = model.with_constituent(name, **_constituent_kwargs(ov, model.by_name(name)))
    return model


def _constituent_kwargs(ov: dict, current) -> dict:
    """Translate a per-constituent override block into ``Constituent`` fields.

    A *partial* law override inherits the coefficients it does not name from the
    constituent's current law, so a single-value command-line override such as
    ``--set model.constituents.collagen.law.c1=600`` works even when the config
    does not spell out the whole law (previously that raised ``KeyError: 'c2'``).
    """
    kw: dict = {}
    if "turnover_days" in ov:
        kw["k_d"] = 1.0 / float(ov["turnover_days"])
    for key in ("k_d", "gain", "G", "phi0", "degradable"):
        if key in ov:
            kw[key] = ov[key]
    if "law" in ov:
        law = ov["law"]
        if "c1" in law or "c2" in law:          # Fung fiber (possibly a partial override)
            base = current.law if isinstance(current.law, FungFiber) else None

            def pick(key: str) -> float:
                if key in law:
                    return float(law[key])
                if base is not None:
                    return float(getattr(base, key))
                raise ValueError(
                    f"a Fung law override needs both c1 and c2 when the constituent's "
                    f"current law is not a Fung fiber: {law}")

            kw["law"] = FungFiber(c1=pick("c1"), c2=pick("c2"))
        elif "c" in law:                        # neo-Hookean
            kw["law"] = NeoHookean(c=float(law["c"]))
        else:
            raise ValueError(f"law override needs c1/c2 (Fung) or c (neo-Hookean): {law}")
    return kw


def build_insult(cfg: dict) -> Insult:
    ic = cfg.get("insult") or {}
    return Insult(
        pressure_factor=float(ic.get("pressure_factor", 1.0)),
        elastin_surviving=float(ic.get("elastin_surviving", 1.0)),
        t_on=float(ic.get("t_on", 0.0)),
        ramp=float(ic.get("ramp", 1.0)),
    )


def build_geometry(cfg: dict, model: Model):
    name = cfg.get("geometry", "artery")
    if name != "artery":
        raise ValueError(f"unknown geometry {name!r} (only 'artery' is supported)")
    return artery(model)


def _sim_kwargs(func, cfg: dict) -> dict:
    """``simulate:`` block filtered to the kwargs ``func`` actually accepts."""
    accepted = set(inspect.signature(func).parameters)
    return {k: v for k, v in (cfg.get("simulate") or {}).items() if k in accepted}


# =============================================================================
# The four study types
# =============================================================================
def run(cfg: dict, *, trace: bool = False, trace_every: float | None = None):
    """Dispatch on ``study:`` and return ``(fig, summary_dict)``.

    ``trace=True`` turns on the live tracker (:mod:`gr.monitor`): the physical
    quantities from the slides are printed as the solver runs.  ``trace_every``
    is the print interval in days (``None`` -> about 25 rows over the run).
    """
    study = cfg["study"]
    if study == "transient":
        return _study_transient(cfg, trace=trace, trace_every=trace_every)
    if study == "compare":
        return _study_compare(cfg, trace=trace, trace_every=trace_every)
    if study == "equilibrium":
        return _study_equilibrium(cfg, trace=trace)
    if study == "map":
        return _study_map(cfg, trace=trace)
    raise ValueError(f"unknown study {study!r}")


def _make_monitor(trace: bool, trace_every: float | None) -> Monitor | None:
    return Monitor(every=trace_every) if trace else None


def _simulate_from(cfg: dict, monitor: Monitor | None = None):
    """Run the single theory named in ``cfg['theory']`` on this config."""
    module = THEORIES[cfg["theory"]]
    model = build_model(cfg)
    geom = build_geometry(cfg, model)
    insult = build_insult(cfg)
    return module.simulate(geom, insult, monitor=monitor, **_sim_kwargs(module.simulate, cfg))


def _sweep_configs(cfg: dict):
    """Yield ``(label, config)`` pairs for a ``sweep:`` block (or a single run)."""
    sw = cfg.get("sweep")
    if not sw:
        yield None, cfg
        return
    param = sw["parameter"]
    for v in _axis_values(sw):
        v = float(v)
        child = copy.deepcopy(cfg)
        child.pop("sweep", None)
        set_by_path(child, param, v)
        yield f"{_short(param)}={v:g}", child


def _study_transient(cfg: dict, *, trace: bool = False, trace_every: float | None = None):
    """One theory over time; overlays one curve per swept value."""
    from .plotting import plt

    print(f"[{cfg.get('title', cfg['theory'])}]  study=transient")
    runs = []
    for label, child in _sweep_configs(cfg):
        if trace and label:
            print(f"\n  ── sweep: {label} ──")
        r = _simulate_from(child, monitor=_make_monitor(trace, trace_every))
        runs.append((label or cfg["theory"], r))

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    cmap = plt.get_cmap("viridis")
    n = len(runs)
    summary = []
    if trace:
        print("\n  final states:")
    for i, (label, r) in enumerate(runs):
        color = cmap(0.15 + 0.7 * i / max(n - 1, 1)) if n > 1 else "black"
        axes[0].plot(r.t, r.sigma_norm, color=color, label=label)
        axes[1].plot(r.t, r.mass, color=color, label=label)
        status = ("runaway (diverged)" if r.diverged
                  else "adapted" if r.converged
                  else "NOT converged (still evolving)")
        summary.append({"label": label, "sigma_norm": float(r.sigma_norm[-1]),
                        "mass": float(r.mass[-1]), "diverged": bool(r.diverged),
                        "converged": bool(r.converged)})
        print(f"  {label:>16}:  sigma/sigma_h -> {r.sigma_norm[-1]:.3f},"
              f"  mass -> {r.mass[-1]:.3f},  {status}")
    axes[0].axhline(1.0, color="gray", lw=1)
    axes[0].set(xlabel="time [day]", ylabel=r"$\bar\sigma/\bar\sigma_h$", title="stress vs set-point")
    axes[1].set(xlabel="time [day]", ylabel=r"mass $M/M_0$", title="growth")
    if n > 1:
        axes[1].legend(title=_short(cfg["sweep"]["parameter"]))
    fig.suptitle(cfg.get("title", ""))
    fig.tight_layout()
    return fig, {"runs": summary}


def _study_compare(cfg: dict, *, trace: bool = False, trace_every: float | None = None):
    """Overlay several theories on the same scenario; report speed and agreement."""
    from .plotting import STYLE, plt

    model = build_model(cfg)
    geom = build_geometry(cfg, model)
    insult = build_insult(cfg)

    results, timings = [], {}
    print(f"[{cfg.get('title', 'compare')}]  study=compare")
    for name in cfg["theories"]:
        module = THEORIES[name]
        t0 = time.perf_counter()
        r = module.simulate(geom, insult, monitor=_make_monitor(trace, trace_every),
                            **_sim_kwargs(module.simulate, cfg))
        timings[r.theory] = time.perf_counter() - t0
        results.append(r)
        print(f"  {r.theory:>18}: {timings[r.theory]:6.2f} s")

    # pairwise agreement of the mass trajectory (aligned on the common length)
    if len(results) >= 2:
        a, b = results[0], results[1]
        m = min(len(a.mass), len(b.mass))
        gap = float(np.max(np.abs(a.mass[:m] - b.mass[:m])))
        print(f"  largest mass-ratio gap ({results[0].theory} vs {results[1].theory}): {gap:.4f}")
    else:
        gap = float("nan")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for r in results:
        style = STYLE.get(r.theory, {})
        axes[0].plot(r.t, r.sigma_norm, label=r.theory, **style)
        axes[1].plot(r.t, r.mass, label=r.theory, **style)
    axes[0].axhline(1.0, color="gray", lw=1)
    axes[0].set(xlabel="time [day]", ylabel=r"$\bar\sigma/\bar\sigma_h$", title="stress")
    axes[1].set(xlabel="time [day]", ylabel=r"$M/M_0$", title="mass")
    axes[1].legend()
    fig.suptitle(cfg.get("title", ""))
    fig.tight_layout()
    return fig, {"timings": timings, "mass_gap": gap}


def _study_equilibrium(cfg: dict, *, trace: bool = False):
    """Instant equilibrated solve; optional scan traces the stability boundary."""
    from .plotting import plt

    model = build_model(cfg)
    geom = build_geometry(cfg, model)
    insult = build_insult(cfg)

    e = equilibrated_cmm.solve(geom, insult)
    print(f"[{cfg.get('title', 'equilibrium')}]  study=equilibrium")
    print(f"  equilibrium exists? {e.exists}")
    if e.exists:
        print(f"  evolved stretch lambda* = {e.lam:.3f},  mass = {e.mass:.3f}")
        # Cross-check the headline claim right here: the equilibrated solve skips the
        # transient but should land on its plateau.  Run the cheap homogenized
        # transient on the same insult and compare, so the student sees the match
        # without having to set up a separate run.
        rt = homogenized_cmm.simulate(geom, insult, t_end=5000, dt=1.0)
        lam_t = float(rt.lam[-1])
        gap = 100.0 * abs(lam_t - e.lam) / e.lam
        settled = "settled" if rt.converged else "still evolving"
        print(f"  transient check: homogenized plateau lambda = {lam_t:.3f} ({settled}) "
              f"-> matches lambda* to {gap:.1f}%")
        if trace:
            # The evolved end state, in the same physical quantities the transient
            # tracker prints: mass fractions phi^k and per-constituent stress.
            tot = sum(e.masses.values())
            fracs = "  ".join(f"φ_{k}={m / tot:.3f}" for k, m in e.masses.items())
            stresses = "  ".join(f"σ_{k}/σh={s:.3f}" for k, s in e.stresses.items())
            print(f"    radius r* = {e.radius:.3f} mm,  thickness h* = {e.thickness:.4f} mm")
            print(f"    mass fractions:  {fracs}")
            print(f"    constituent stress:  {stresses}")

    summary = {"exists": e.exists, "lam": float(e.lam)}
    if e.exists:
        summary["transient_lam"] = lam_t

    fig = None
    scan = cfg.get("scan")
    if scan:
        param = scan["parameter"]
        values = _axis_values(scan)
        if trace:
            print(f"\n  scanning {_short(param)} over {len(values)} values "
                  f"[{values[0]:g} → {values[-1]:g}] for the stability boundary:")
        lam = []
        n_exist = 0
        step = max(1, len(values) // 12)
        for idx, v in enumerate(values):
            child = copy.deepcopy(cfg)
            set_by_path(child, param, float(v))
            ev = equilibrated_cmm.solve(build_geometry(child, build_model(child)),
                                        build_insult(child))
            lam.append(ev.lam if ev.exists else np.nan)
            n_exist += int(ev.exists)
            if trace and (idx % step == 0 or idx == len(values) - 1):
                state = f"λ*={ev.lam:.3f}" if ev.exists else "no equilibrium (runaway)"
                print(f"      {_short(param)}={v:6.3f}  →  {state}")
        if trace:
            print(f"    equilibrium exists for {n_exist}/{len(values)} scanned values")
        fig, ax = plt.subplots(figsize=(7, 4.6))
        ax.plot(values, lam, color="#C44E52", lw=2.5)
        ax.set(xlabel=_short(param), ylabel=r"evolved stretch $\lambda^*$",
               title=cfg.get("title", "equilibrated existence"))
        if cfg.get("report_critical") == "elastin":
            s_crit = critical_elastin_loss(geom)
            summary["critical_elastin"] = float(s_crit)
            ax.axvline(s_crit, color="gray", ls="--", label=f"boundary ~ {100 * s_crit:.0f}%")
            ax.legend()
            print(f"  critical surviving elastin = {100 * s_crit:.1f} %")
        fig.tight_layout()

    return fig, summary


def _study_map(cfg: dict, *, trace: bool = False):
    """2-D existence grid: does an equilibrium exist over two swept axes?"""
    from .plotting import plt

    ax_spec = cfg["axes"]
    xs = _axis_values(ax_spec["x"])
    ys = _axis_values(ax_spec["y"])
    px, py = ax_spec["x"]["parameter"], ax_spec["y"]["parameter"]

    print(f"[{cfg.get('title', 'stability map')}]  study=map")
    if trace:
        print(f"  sweeping {_short(px)} × {_short(py)} on a {len(xs)}×{len(ys)} grid "
              f"({len(xs) * len(ys)} equilibrated solves):")
    Z = np.zeros((len(ys), len(xs)))
    for j, yv in enumerate(ys):
        for i, xv in enumerate(xs):
            child = copy.deepcopy(cfg)
            set_by_path(child, px, float(xv))
            set_by_path(child, py, float(yv))
            model = build_model(child)
            Z[j, i] = adapts(build_geometry(child, model), build_insult(child))
        if trace:
            row_frac = float(Z[j].mean())
            print(f"      {_short(py)}={yv:6.3f}  ({j + 1:>3}/{len(ys)} rows)  "
                  f"→  {row_frac * 100:3.0f}% of this row adapts")

    frac = float(Z.mean())
    print(f"  fraction of the grid that ADAPTS: {frac:.2f}  (bigger = more stable)")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.contourf(xs, ys, Z, levels=[-0.5, 0.5, 1.5], colors=["#F4C7C3", "#CFE3F5"])
    ax.contour(xs, ys, Z, levels=[0.5], colors="k")
    ax.set(xlabel=_short(px), ylabel=_short(py), title=cfg.get("title", "stable vs unstable"))
    fig.tight_layout()
    return fig, {"fraction_adapts": frac}

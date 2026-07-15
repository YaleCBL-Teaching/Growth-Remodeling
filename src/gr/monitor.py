r"""
A tiny, dependency-free **live tracker** for a running G&R solve.

The four theories otherwise run silently and only print a one-line summary at the
end.  When you hand a :class:`Monitor` to ``simulate(...)`` (via ``run.py
--trace`` or ``run_all.py``) it prints, as the solver marches in time, the very
quantities the slides introduce:

    time  |  stretch lambda  |  tissue stress sigma/sigma_h  |  total mass M/M_0
          |  per-constituent MASS FRACTIONS phi^k = M^k / M_tot
          |  per-constituent production STIMULUS  Upsilon^k = 1 + K_sigma (sigma/sigma_h - 1)
          |  mid-wall radius r  |  wall thickness h

so you can *watch* the wall thicken, the collagen fraction rise, and the stimulus
relax back to 1 as the tissue adapts (or run away when it does not).

Nothing here is theory-specific: a solver calls :meth:`Monitor.begin` once with
its own columns, then :meth:`Monitor.row` every step (the monitor throttles the
output to a readable number of lines) and :meth:`Monitor.end` once at the finish.
The helpers :func:`cmm_columns` and :func:`driving_preamble` build the standard
constrained-mixture layout shared by the full and homogenized models.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TextIO

# Compact, fixed labels so per-constituent columns stay narrow in the table.
_ABBREV = {"elastin": "ela", "collagen": "col", "smc": "smc"}


def _ab(name: str) -> str:
    return _ABBREV.get(name, name[:3])


@dataclass
class Column:
    """One column of the live table: where to read it, how to label and format it."""

    key: str                 # key into the per-step values dict
    header: str              # column header
    fmt: str = "{:.3f}"      # format applied to the value
    width: int = 0           # 0 -> sized automatically from the header


class Monitor:
    r"""Throttled, tabular progress print for a time-marching solve.

    Parameters
    ----------
    every : float | None
        Print a row only after this many **days** of simulated time have passed
        since the last one (the first and last steps always print).  ``None``
        means *auto*: about 25 rows over the run, chosen in :meth:`begin` from the
        total time span.
    enabled : bool
        A disabled monitor is a no-op, so solvers can always call it
        unconditionally.
    stream : text stream
        Where to write (defaults to ``sys.stdout``).
    """

    def __init__(self, *, every: float | None = None, enabled: bool = True,
                 stream: TextIO | None = None):
        self.every = every
        self.enabled = enabled
        self.stream = stream or sys.stdout
        self._cols: list[Column] = []
        self._last: float | None = None
        self._last_row: str | None = None   # last emitted line (for de-duplication)
        self._started = False

    # -- lifecycle ------------------------------------------------------------
    def begin(self, title: str, columns, preamble=(), *, t_span: float | None = None) -> None:
        """Print the banner + column header and fix the table layout."""
        if not self.enabled:
            return
        if self.every is None:
            self.every = (t_span / 25.0) if t_span else 100.0
        self._cols = [c if isinstance(c, Column) else Column(*c) for c in columns]
        for c in self._cols:
            c.width = max(c.width, len(c.header), 6)
        w = self.stream.write
        w(f"\n  ▶ {title}\n")
        for line in preamble:
            w(f"      {line}\n")
        header = "  ".join(c.header.rjust(c.width) for c in self._cols)
        w("      " + header + "\n")
        w("      " + "-" * len(header) + "\n")
        self._started = True
        self._last = None
        self._last_row = None

    def row(self, t: float, values: dict, *, force: bool = False, note: str = "") -> None:
        """Print one row iff enough simulated time has elapsed (or ``force``).

        Consecutive rows identical to the last printed one are suppressed, so a
        long steady state does not scroll off the screen; the first change after
        it prints again, and :meth:`end` always prints the final state.
        """
        if not (self.enabled and self._started):
            return
        if not (force or self._last is None or (t - self._last) >= self.every):
            return
        self._last = t
        line = self._format(values)
        if line != self._last_row:
            self._write(line)

    def end(self, t: float, values: dict, note: str = "") -> None:
        """Always print a final row (the adapted / diverged end state)."""
        if not (self.enabled and self._started):
            return
        self._last = t
        self._write(self._format(values, note))

    # -- internals ------------------------------------------------------------
    def _format(self, values: dict, note: str = "") -> str:
        cells = []
        for c in self._cols:
            v = values.get(c.key)
            try:
                s = c.fmt.format(v) if v is not None else "-"
            except (ValueError, TypeError):
                s = str(v)
            cells.append(s.rjust(c.width))
        row = "      " + "  ".join(cells)
        return row + "   " + note if note else row

    def _write(self, line: str) -> None:
        self._last_row = line
        self.stream.write(line + "\n")
        flush = getattr(self.stream, "flush", None)
        if flush:
            flush()


# =============================================================================
# Standard layouts for the constrained-mixture models
# =============================================================================
def cmm_columns(constituents, turnover) -> list[Column]:
    r"""Columns for a constrained-mixture solve: state, mass fractions, stimuli.

    ``constituents`` gets one mass-fraction column phi^k each; the turnover
    constituents additionally get a production-stimulus column Upsilon^k (elastin
    has no stimulus -- it neither turns over nor is produced).
    """
    cols = [
        Column("t", "t[day]", "{:.0f}"),
        Column("lam", "λ", "{:.3f}"),
        Column("sig", "σ/σh", "{:.3f}"),
        Column("mass", "M/M0", "{:.3f}"),
    ]
    cols += [Column(f"phi_{c.name}", f"φ_{_ab(c.name)}", "{:.3f}") for c in constituents]
    cols += [Column(f"ups_{c.name}", f"Υ_{_ab(c.name)}", "{:.3f}") for c in turnover]
    cols += [Column("r", "r[mm]", "{:.3f}"), Column("h", "h[mm]", "{:.4f}")]
    return cols


def driving_preamble(model, insult) -> list[str]:
    """Human-readable description of the insult and the homeostatic set-point."""
    lines: list[str] = []
    if insult.pressure_factor != 1.0:
        lines.append(f"insult: pressure ×{insult.pressure_factor:g} "
                     f"from t={insult.t_on:g} d (ramp {insult.ramp:g} d)")
    if insult.elastin_surviving != 1.0:
        lines.append(f"insult: elastin → {100 * insult.elastin_surviving:.0f}% surviving "
                     f"from t={insult.t_on:g} d (ramp {insult.ramp:g} d)")
    if not lines:
        lines.append("insult: none (homeostatic baseline)")
    lines.append(f"set-point: σh = {model.sigma_bar_h:.1f} kPa,  "
                 f"R = {model.R:.2f} mm,  H = {model.H:.3f} mm")
    return lines


def status_note(diverged: bool, converged: bool = True) -> str:
    """The final-row tag: adapted vs. (hard or slow) runaway.

    ``diverged`` is the hard runaway (stretch hit the cutoff).  ``converged=False``
    without divergence is the *slow* runaway: stress is held near the set-point by
    mass that is still growing at the end of the window -- it has NOT adapted.
    """
    if diverged:
        return "⚠ diverged — runaway (no equilibrium)"
    if converged:
        return "✓ adapted"
    return "… not converged — still evolving (try a larger simulate.t_end)"

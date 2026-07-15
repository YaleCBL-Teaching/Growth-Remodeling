# Growth & Remodeling of Soft Tissue — a hands-on seminar

A 3-hour introduction, for an engineering audience, to how living cardiovascular
tissues adapt their **mass, composition, and microstructure** to mechanical load,
and to the four modelling frameworks that describe it:

1. **Kinematic growth** (Rodriguez, Hoger & McCulloch 1994)
2. **Constrained mixture** — full heredity integrals (Humphrey & Rajagopal 2002)
3. **Homogenized constrained mixture** (Cyron, Aydin & Humphrey 2016)
4. **Equilibrated constrained mixture** (Latorre & Humphrey 2018)

All four run on **one shared set of parameters** and **one shared mechanical
setting**, so every comparison is apples-to-apples. They are deliberately
reduced-order (1D, single stress component) so the essential behaviour fits on a
screen and runs in seconds; `docs/` and the code comments point to the full
tensorial equations.

The one big question: **when does a loaded tissue adapt to a stable new state, and
when does it grow without bound (aneurysm)?**

| Theory | Stability behaviour you will observe |
|---|---|
| **Kinematic growth** | Converges to the *prescribed* homeostatic stress, or runs away — stability is imposed, not predicted. |
| **Constrained mixture (full)** | Stability is *predicted* from turnover and **depends on the insult**: mild → adapts, severe → runaway. |
| **Homogenized CMM** | Follows the full model's **time trajectory** closely, at a fraction of the cost. |
| **Equilibrated CMM** | **Matches** the transient theories *if an equilibrium exists* — and flags, by having no solution, when one does not. |

## Setup

```bash
uv sync                 # create .venv and install everything from uv.lock
```

Dependencies are only NumPy, SciPy, Matplotlib, and PyYAML; no LaTeX install is
needed (figures use Matplotlib mathtext). Prefix commands with `uv run`, or
activate the environment once with `source .venv/bin/activate`.

## Running an exercise

Each exercise is a small **YAML input file** in `configs/`; one `run.py` drives
them all — you never edit Python. Change a value in the file, or override it on
the command line:

```bash
# run an exercise as-is:
uv run python run.py configs/ex01_kinematic_growth.yaml

# parametric study — one overlaid curve per value:
uv run python run.py configs/ex01_kinematic_growth.yaml --sweep insult.pressure_factor=1.5,2,3

# override any single value (dotted path into the config):
uv run python run.py configs/ex02_constrained_mixture.yaml --set model.constituents.collagen.gain=3.0

# save the figure instead of showing it:
uv run python run.py configs/ex05_stability.yaml --save out/ex05.pdf --no-show
```

A config picks the `study` (`transient`, `compare`, `equilibrium`, or `map`), the
`theory`, `geometry`, `insult`, and parameters; a `sweep:` block (or `--sweep`)
turns any parameter into an overlaid study. See the comments in each
`configs/*.yaml` and the schema atop [`src/gr/scenario.py`](src/gr/scenario.py).

### Watch the physics as it solves (`--trace`)

Add `--trace` to stream the quantities from the slides as the solver marches in
time — stretch `λ`, tissue stress `σ/σh`, total mass `M/M0`, per-constituent
**mass fractions** `φ`, production **stimuli** `Υ`, and the wall radius/thickness:

```
  ▶ full CMM · artery
      insult: pressure ×1.5 from t=1 d (ramp 1 d)
      set-point: σh = 102.4 kPa,  R = 1.00 mm,  H = 0.130 mm
      t[day]       λ    σ/σh    M/M0   φ_ela   φ_col   φ_smc   Υ_col   Υ_smc   r[mm]   h[mm]
           0   1.000   1.000   1.000   0.300   0.350   0.350   1.000   1.000   1.000  0.1299
         200   1.033   0.998   1.603   0.187   0.406   0.406   0.998   0.998   1.033  0.2016
         400   1.027   0.999   1.583   0.190   0.405   0.405   0.999   0.999   1.027  0.2003   ✓ adapted
```

The `equilibrium` and `map` studies trace their scan progress instead. Control
the row interval with `--trace-every DAYS`.

### Run every slide exercise at once

```bash
uv run python run_all.py               # ex01..ex05 with --trace, figures to out/
uv run python run_all.py --no-trace    # end-of-run summaries only
uv run python run_all.py --only ex02   # just one (substring match)
```

## Repository layout

```
src/gr/      the maths and the four models (read, don't edit; comments tie each line to an equation)
docs/        lecture notes: biology, finite-strain theory, one file per theory, the stability capstone
configs/     student input files — one small YAML per exercise
run.py       one runner for every exercise;  run_all.py runs them all
exercises/   the same exercises as annotated standalone scripts
solutions/   teacher scripts; regenerate the slide figures into docs/figures/
slides/      the LaTeX deck (student + teacher builds)
```

Students run `configs/` with `run.py` and read `docs/`; instructors run
`solutions/` to regenerate figures.

## Suggested 3-hour flow

| Read | then run |
|---|---|
| `docs/01_biology.md`, `docs/02_finite_strain.md` | `exercises/ex00_biology_and_mechanics.py` (materials plot) |
| `docs/03_kinematic_growth.md` | `run.py configs/ex01_kinematic_growth.yaml` |
| `docs/04_constrained_mixture.md` | `run.py configs/ex02_constrained_mixture.yaml` |
| `docs/05_homogenized_cmm.md` | `run.py configs/ex03_homogenized_vs_full.yaml` |
| `docs/06_equilibrated_cmm.md` | `run.py configs/ex04_equilibrated.yaml` |
| `docs/07_stability.md` | `run.py configs/ex05_stability.yaml` |

Part 1 (kinematic growth + full mixture) then, after a short break, Part 2
(homogenized, equilibrated, and the stability capstone).

## Teacher tooling

```bash
uv run python solutions/make_all_figures.py    # regenerate docs/figures/*.pdf
uv run python solutions/_check_models.py        # quick numerical self-check
uv sync --extra video                           # add bundled ffmpeg for MP4 (optional)
uv run python solutions/make_all_videos.py      # animated twins -> docs/videos/*.mp4
```

The videos are animated twins of the figures, built from the same `Result`
objects the models return, so the numbers match exactly. See
[`docs/videos/`](docs/videos/README.md).

## References

- Rodriguez EK, Hoger A, McCulloch AD. *Stress-dependent finite growth in soft
  elastic tissues.* J Biomech 27:455–467, 1994.
- Humphrey JD, Rajagopal KR. *A constrained mixture model for growth and
  remodeling of soft tissues.* Math Models Methods Appl Sci 12:407–430, 2002.
- Cyron CJ, Aydin RC, Humphrey JD. *A homogenized constrained mixture (and
  mechanical analog) model for growth and remodeling of soft tissue.* Biomech
  Model Mechanobiol 15:1389–1403, 2016.
- Latorre M, Humphrey JD. *Mechanobiological stability of biological soft
  tissues.* J Mech Phys Solids 125:298–325, 2019.
- Ambrosi D et al. *Growth and remodelling of living tissues: perspectives,
  challenges and opportunities.* J R Soc Interface 16:20190233, 2019.
- Humphrey JD. *Constrained Mixture Models of Soft Tissue Growth and Remodeling
  — Twenty Years After.* J Elasticity 145:49–75, 2021.

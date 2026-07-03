# Growth & Remodeling of Soft Tissue — a hands-on seminar

A 3-hour introduction, for an engineering audience, to how living cardiovascular
tissues adapt their **mass, composition, and microstructure** to mechanical
load — and to the four modelling frameworks that describe it:

1. **Kinematic growth** (Rodriguez, Hoger & McCulloch 1994)
2. **Constrained mixture** — full heredity integrals (Humphrey & Rajagopal 2002)
3. **Homogenized constrained mixture** (Cyron, Aydin & Humphrey 2016)
4. **Equilibrated constrained mixture** (Latorre & Humphrey 2018)

All four are implemented on **one shared set of parameters** and **one shared
mechanical setting**, so every comparison is apples-to-apples. You drive the same
tissue with the same insults and watch the theories agree — or disagree.

> These are deliberately **reduced-order (1D / thin-membrane, single stress
> component)** versions of the full theories, chosen so the essential behaviour
> fits on a screen and runs in seconds. The code comments and `docs/` point to
> the full tensorial equations and the papers.

---

## The one big question

> **When does a loaded tissue adapt to a stable new state, and when does it lose
> stability and grow without bound (aneurysm)?**

What you will take away, and can reproduce yourself in the exercises:

| Theory | Stability behaviour you will observe |
|---|---|
| **Kinematic growth** | Either it converges to the *prescribed* homeostatic stress, or it runs away — stability is imposed, not predicted. |
| **Constrained mixture (full)** | Stability is *predicted* from turnover and **depends on the insult**: mild → adapts, severe → runaway. |
| **Homogenized CMM** | Follows the full model's **time trajectory** closely, at a fraction of the cost. |
| **Equilibrated CMM** | **Matches** the transient theories *if an equilibrium exists* — and tells you (by having no solution) when one does not. |

---

## Repository layout — three kinds of file

```
src/gr/          FUNDAMENTALS  — the maths and the four models.  Read them; you
                 don't need to edit them.  Comments tie each line to an equation.
docs/            The lecture notes: biology, finite-strain theory, one file per
                 theory, plus the stability capstone.  Equations + figures.
exercises/       STUDENT files.  Each is a short script with a clearly marked
                 "YOUR TURN" block: change a parameter, add a sweep, make a plot.
solutions/       TEACHER files.  Fully worked; running them writes the
                 presentation-ready PDFs into docs/figures/.
```

If you are a **student**, live in `exercises/` (and read `docs/`).
If you are the **instructor**, run `solutions/` to regenerate every figure.

---

## Setup

### Option A — `uv` (recommended)

```bash
uv venv                 # create .venv
uv pip install -e .     # install the gr package (editable)
uv run python exercises/ex01_biology_and_mechanics.py
```

or activate the environment once and use plain `python`:

```bash
source .venv/bin/activate
python exercises/ex01_biology_and_mechanics.py
```

### Option B — conda

```bash
conda env create -f environment.yml
conda activate growth-remodeling
pip install -e .
python exercises/ex01_biology_and_mechanics.py
```

Dependencies are only **NumPy, SciPy, and Matplotlib**. No LaTeX install is
needed (figures use Matplotlib mathtext).

---

## Suggested 3-hour flow

**Part 1 (90 min) — foundations & the first two theories**

1. `docs/01_biology.md` — why tissues grow and remodel (no maths).
2. `docs/02_finite_strain.md` — the minimum continuum mechanics.
   → `exercises/ex01_biology_and_mechanics.py`
3. `docs/03_kinematic_growth.md` — multiplicative growth.
   → `exercises/ex02_kinematic_growth.py`
4. `docs/04_constrained_mixture.md` — turnover & heredity integrals.
   → `exercises/ex03_constrained_mixture.py`

*— 3-minute break —*

**Part 2 (90 min) — approximations, equilibrium, and stability**

5. `docs/05_homogenized_cmm.md` — temporal homogenization.
   → `exercises/ex04_homogenized_vs_full.py`
6. `docs/06_equilibrated_cmm.md` — skip the transient.
   → `exercises/ex05_equilibrated.py`
7. `docs/07_stability.md` — the capstone: adaptation vs. aneurysm.
   → `exercises/ex06_stability_and_aneurysm.py`

Each exercise has a matching `solutions/figXX_*.py` that produces the slide
figure for that step.

---

## Regenerate every lecture figure at once

```bash
uv run python solutions/make_all_figures.py
# -> writes docs/figures/*.pdf
```

## Animated videos

Every simulation figure also has an animated twin — a deforming vessel next to
the response curves, with the insult drawn over time so the **immediate elastic**
jump is separated from the slow **growth & remodeling**. They are built from the
same `Result` objects the models return (`gr.animation`), so the numbers match
the figures exactly. See [`docs/videos/`](docs/videos/README.md).

```bash
uv pip install -e ".[video]"                    # bundled ffmpeg for MP4 (optional)
uv run python solutions/make_all_videos.py      # -> docs/videos/*.mp4
```

## Sanity check the models

```bash
uv run python -m pytest -q        # if you add tests, or:
uv run python solutions/_check_models.py   # quick numerical self-check
```

---

## Cross-validation against svGrowth

The `comparison/` directory (on the `svgrowth-comparison` branch) reproduces the
hypertension exercise with [**svGrowth**](https://github.com/StanfordCBCL/svGrowth),
a research-grade constrained-mixture framework, and checks that the two codes
agree. Configured to the same problem, the `gr` 1-D model and svGrowth's biaxial
thin-wall model track each other's normalised adaptation closely (inner radius to
<1%, other quantities to a few percent). See
[`comparison/README.md`](comparison/README.md) for setup, the matched
configuration, and the residual-difference discussion.

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

# Seminar slides — Growth & Remodeling of Soft Tissue

Beamer slides for the G&R seminar, in two builds:

- **`gr-seminar-student.pdf`** — key equations are shown as **empty numbered
  boxes** to fill in during class (e.g. on an iPad). Distribute this version to
  students beforehand.
- **`gr-seminar-teacher.pdf`** — the same boxes are **filled in** with the
  actual equations.

Both are 16:9 and carry a per-slide source citation in the format
*First, …, Last, short journal (year)*.

## Build

Requires a TeX installation with `beamer` on `PATH` (any recent TeX Live / MacTeX).

```sh
make            # both PDFs
make student    # gr-seminar-student.pdf
make teacher    # gr-seminar-teacher.pdf
make figures    # regenerate the reproducible result figures from the gr package
make clean
```

## How the fill-in mechanism works

`theme/preamble.tex` defines

```latex
\slboxeq{<box height>}{<eq label>}{<equation body>}
```

The `\teachertrue` / `\teacherfalse` toggle in `slides-teacher.tex` /
`slides-student.tex` selects whether each `\slboxeq` renders the boxed, numbered
equation (teacher) or an empty numbered box at the same position (student). The
equation number and every `\eqref` are identical in both builds, so the two PDFs
stay in lock-step.

## Reproducible figures

The result figures (`fig01`–`fig06`, `fig_svgrowth_comparison`) are produced by
the `gr` package in this repository:

```sh
python solutions/make_all_figures.py   # or: uv run python solutions/make_all_figures.py
```

`make figures` runs this and copies the PDFs into `figures/`, so the deck never
drifts from the model. Schematic and hand-annotated figures are adapted from
lecture material (A. Gebauer, TUM) and prior talks (M. Pfaller); literature
figures are cited per slide.

## Layout

```
slides/
  slides-student.tex   slides-teacher.tex   # master files (mode toggle)
  body.tex                                  # title, roadmap, section inputs
  theme/preamble.tex                        # theme + \slboxeq mechanism
  sections/01_biology.tex … 11_summary.tex  # the 11 sections
  figures/                                  # result + talk + literature figures
  references.bib                            # consolidated bibliography
  Makefile
```

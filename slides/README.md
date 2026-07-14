# Seminar slides — Growth & Remodeling of Soft Tissue

Beamer slides for the G&R seminar, in two builds:

- **`gr-seminar-student.pdf`** — the content is revealed **piece by piece**
  (beamer overlays), so it builds up step by step as you present.
- **`gr-seminar-teacher.pdf`** — the **whole slide** is shown at once (a static
  reference with everything visible).

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

## How the build mechanism works

`theme/preamble.tex` defines a reveal step, `\srev` (nothing in the teacher
build, `\pause` in the student build), and the equation helpers

```latex
\slboxeq{<eq label>}{<equation body>}   % numbered key equation; its own reveal step
\keyeq{<eq label>}{<equation body>}     % numbered equation, no reveal (for use in boxes)
\giveneq{<equation body>}               % unnumbered equation; also a reveal step
```

The `\teachertrue` / `\teacherfalse` toggle in `slides-teacher.tex` /
`slides-student.tex` selects the mode: teacher shows the whole slide at once,
student reveals each `\srev`/equation as a separate overlay. Equation numbers and
every `\eqref` are identical in both builds, so the two PDFs stay in lock-step.
Add `\srev` between text pieces (at frame level) to build them up too.

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
  theme/preamble.tex                        # theme + student/teacher reveal mechanism
  sections/01_biology.tex … 11_summary.tex  # the 11 sections
  figures/                                  # result + talk + literature figures
  references.bib                            # consolidated bibliography
  Makefile
```

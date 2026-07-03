# ============================================================================
#  Growth & Remodeling seminar slides — student & teacher builds
#
#  Requires a TeX installation with beamer on PATH. On this host use MacTeX:
#      export PATH="/Library/TeX/texbin:$PATH"
#
#  Targets:
#      make            -> both PDFs
#      make student    -> gr-seminar-student.pdf  (empty formula boxes)
#      make teacher    -> gr-seminar-teacher.pdf  (formulas filled in)
#      make figures    -> regenerate the reproducible result figures via the gr package
#      make clean      -> remove LaTeX aux files
# ============================================================================
LATEX   := pdflatex -interaction=nonstopmode -halt-on-error
PYTHON  ?= python3

.PHONY: all student teacher figures clean

all: student teacher

student: slides-student.tex body.tex theme/preamble.tex $(wildcard sections/*.tex)
	$(LATEX) slides-student.tex
	$(LATEX) slides-student.tex
	cp slides-student.pdf gr-seminar-student.pdf

teacher: slides-teacher.tex body.tex theme/preamble.tex $(wildcard sections/*.tex)
	$(LATEX) slides-teacher.tex
	$(LATEX) slides-teacher.tex
	cp slides-teacher.pdf gr-seminar-teacher.pdf

# Regenerate the reproducible result figures (fig01-06 + svGrowth comparison)
# from the gr package, then copy the PDFs into figures/ so the slides stay in
# sync with the code. Run from the repository root's environment.
figures:
	cd .. && $(PYTHON) solutions/make_all_figures.py
	cp ../docs/figures/*.pdf figures/

clean:
	rm -f *.aux *.log *.nav *.snm *.toc *.out *.vrb *.fls *.fdb_latexmk

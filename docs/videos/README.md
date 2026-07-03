# Animated videos

Each video is the animated twin of a static figure, built from the **same
simulation results** (`gr.animation` consumes the models' `Result` objects). All
three parts are synchronized:

- a **deforming vessel** whose radius / wall thickness track the simulation,
  tinted by the current stress relative to homeostatic (red = elevated, grey =
  restored);
- the **insult** drawn over time, so the *immediate elastic* jump (when the load
  steps) is visually separated from the slow **growth & remodeling** that follows;
- the **response** curves, revealed live with a moving time cursor.

| video | twin of | what it shows |
|---|---|---|
| `video02_kinematic_growth.mp4` | fig02 | kinematic growth restoring the prescribed set-point under hypertension |
| `video03_constrained_mixture.mp4` | fig03 | full-CMM turnover: collagen & SMC grow, elastin is diluted |
| `video04_compare_hypertension.mp4` | fig04 (top) | four theories adapting to hypertension; converging onto the equilibrated target |
| `video04_compare_aneurysm.mp4` | fig04 (bottom) / fig05 | four theories under a mild aneurysm (elastin → 30%), settling onto the equilibrated line |
| `video06_runaway_aneurysm.mp4` | fig06 (unstable) | severe elastin loss (→ 3%): no equilibrium exists, the vessel dilates without bound |

Regenerate them all with:

```bash
uv pip install -e ".[video]"           # bundled ffmpeg for MP4 (optional)
uv run python solutions/make_all_videos.py          # -> docs/videos/*.mp4
uv run python solutions/make_all_videos.py --gif    # -> *.gif (inline-previewable)
```

> GitHub does not autoplay committed `.mp4` inline in Markdown — click a file
> above to view it, or generate GIFs with `--gif` for inline previews. The MP4s
> embed directly in Keynote / PowerPoint for the lecture.

Non-time figures (fig00 setup, fig01 constitutive laws, and the parameter-sweep
panels of fig05/fig06) have no "live" analogue and stay as figures.

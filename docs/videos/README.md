# Animated videos

Each video is the animated twin of a static figure, built from the **same
simulation results** (`gr.animation` consumes the models' `Result` objects). The
layout is a **16:9 grid**: a large **vessel** cross-section on the left and a grid
of **live plots** on the right (the insult is one of the plots, animated like the
rest). The raw simulation is played over its active window — frames are dense
early and the flat tail is cropped.

The vessel is drawn with a **light-gray current wall** about the mid-wall radius
and a bold **red reference outline** (fixed), so the change from the reference
configuration is easy to see. The response panels depend on the video:

- **single-theory** videos plot the **per-constituent** stress
  $\sigma^k/\sigma_h^k$ and mass $M^k/M_0$ — each constituent has its own
  homeostatic stress, so you see collagen and smooth muscle **remodel back** to
  $\sigma_h^k$ while **elastin cannot** (its stress stays elevated, and in the
  aneurysm case runs away — the mechanistic signature of the instability);
- **comparison** videos plot the geometry (mid-wall radius, wall thickness) and
  total mass across the theories, with the reference and equilibrated targets
  marked.

A single shared legend sits outside the panels.

| video | twin of | what it shows |
|---|---|---|
| `video02_kinematic_growth.mp4` | fig02 | kinematic growth under hypertension: per-constituent stresses all return to homeostatic as the wall thickens |
| `video03_constrained_mixture.mp4` | fig03 | full-CMM turnover: collagen & SMC stresses remodel back to σ_h^k (and grow in mass); elastin stress stays elevated |
| `video04_compare_hypertension.mp4` | fig04 (top) | four theories adapting to hypertension (mass, mid-wall radius, thickness), converging onto the equilibrated target |
| `video04_compare_aneurysm.mp4` | fig04 (bottom) / fig05 | four theories under a mild aneurysm (elastin → 30%): mass drops then rebuilds, settling onto the equilibrated line |
| `video06_runaway_aneurysm.mp4` | fig06 (unstable) | severe elastin loss (→ 3%): elastin stress runs away without bound — the mechanistic signature of the instability |

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

# Animated videos

Each video is the animated twin of a static figure, built from the **same
simulation results** (`gr.animation` consumes the models' `Result` objects). The
timeline is split into three clearly labelled phases so you can tell apart what is
**reference**, what is **elastic**, and what is **G&R**:

1. **Reference** — the homeostatic state, no insult.
2. **Elastic** — the insult is applied with G&R switched *off* (at "negative
   time"): an instantaneous mechanical response. For an aneurysm this already
   removes elastin mass, so the mass drops here before G&R rebuilds it.
3. **G&R** — growth & remodeling is switched on (t ≥ 0) and the tissue slowly
   adapts. Frames are dense early and the time axis is cropped to the active
   window, so the video does not sit on a flat tail.

Each frame shows a **deforming vessel** (Stanford-red lumen, thick inner/outer
walls) with a dashed **reference** outline so the change from reference is always
visible, the **insult** drawn over time, and the **response** curves revealed live.

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

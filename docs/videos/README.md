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

- **single-theory** constrained-mixture videos plot the **per-constituent** stress
  $\sigma^k/\sigma_h^k$ and mass $M^k/M_0$ (plus the radius and thickness ratios)
  — each constituent has its own homeostatic stress, so you see collagen and
  smooth muscle **remodel back** to $\sigma_h^k$ while **elastin cannot** (its
  stress stays elevated, and in the severe-aneurysm case runs away — the
  mechanistic signature of the instability). **Kinematic growth is a single
  material**, so its video shows one **wall stress** $\sigma/\sigma_h$ instead (no
  constituents). All single-theory videos use the **full CMM**;
- **comparison** videos plot the geometry (radius ratio $a/a_0$, thickness ratio
  $h/h_0$) and mass ratio $M/M_0$ across the theories, with the reference and
  equilibrated targets marked. The **homogenized** and **equilibrated** CMM appear
  **only** in these comparison videos (they are approximations of the full CMM);
  everywhere else we show the full CMM directly.

**Colours.** Two disjoint palettes are used so nothing is ambiguous. In the
per-constituent panels the constituents are **elastin** (blue, solid),
**collagen** (orange, *dashed* so it never hides behind smooth muscle) and
**smooth muscle** (green, solid); the aggregate geometry curves (radius,
thickness) are drawn in a neutral blue. In the comparison panels the *theories*
get their own separate palette — kinematic growth (purple), full CMM (gold),
homogenized CMM (magenta, dashed), equilibrated CMM (red, dotted) — chosen not to
collide with the constituent colours. The insult is always plain black.

A single shared legend sits outside the panels.

| video | twin of | what it shows |
|---|---|---|
| `video02_kinematic_growth.mp4` | fig02 | kinematic growth (single material) under hypertension: wall stress $\sigma/\sigma_h$ returns to homeostatic as the wall thickens |
| `video03_constrained_mixture.mp4` | fig03 | full-CMM turnover under hypertension: collagen & SMC stresses remodel back to $\sigma_h^k$ (and grow in mass); elastin stress stays elevated |
| `video04_compare_hypertension.mp4` | fig04 (top) | four theories adapting to hypertension (mass, mid-wall radius, thickness), converging onto the equilibrated target |
| `video04_compare_aneurysm.mp4` | fig04 (bottom) / fig05 | the three **constrained-mixture** theories under a mild aneurysm (elastin → 30%) — kinematic growth is dropped (an elastin-loss insult is meaningless for a single material); mass drops then rebuilds, settling onto the equilibrated line |
| `video05_stable_aneurysm.mp4` | — | full CMM, mild aneurysm (elastin → 30%): a **stable** adaptation — collagen & SMC remodel back, elastin stress plateaus, geometry settles to a new equilibrium |
| `video06_runaway_aneurysm.mp4` | fig06 (unstable) | full CMM, severe elastin loss (→ 3%): elastin stress runs away without bound — no equilibrium, the mechanistic signature of the instability |

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

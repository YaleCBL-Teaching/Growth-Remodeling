# 7. Capstone — stability: adaptation vs. aneurysm

*Code: [`gr/stability.py`](../src/gr/stability.py). This ties the whole lecture
together.*

---

## 7.1 The question, restated precisely

A tissue is **mechanobiologically stable** if, after a sustained insult, it
settles at a new bounded equilibrium. It is **unstable** if it grows without
bound. The central result of the modern G&R literature — and of this course — is
that **stability depends on the insult** (and on the tissue's gain and
stiffness), and can be *predicted*.

## 7.2 Where instability comes from: the Laplace exponent

Recall the required-stress law ([§2](02_finite_strain.md),
[`gr/geometry.py`](../src/gr/geometry.py)):

$$\text{artery (Laplace):}\quad \sigma_{\text{req}} \propto \frac{\lambda^2}{M/M_0}.$$

Growth adds mass ($M\uparrow$), which lowers the required stress — a **stabilising
negative feedback**. But dilation ($\lambda\uparrow$) *raises* the required
stress, and in the artery it does so quadratically (Laplace). When elastin — the
tissue's low-stretch load-bearing buffer — is lost, dilation wins the race
against mass production, and the feedback turns positive: **runaway**. It is the
quadratic Laplace exponent that makes this race losable at all.

## 7.3 Two ways to read stability

**(1) Existence of an equilibrium (instant).** From [§6](06_equilibrated_cmm.md),
the equilibrated equation (6.1) has a root iff the tissue can adapt. Sweeping the
insult traces the stable/unstable boundary with no time integration
([`gr.stability.adapts`](../src/gr/stability.py)).

**(2) Watching the transient.** Integrate the homogenized (or full) model: a
stable insult plateaus, an unstable one climbs without bound. Near the boundary
the transient slows down dramatically (critical slowing) — so (1) is the
practical tool and (2) is the confirmation.

![Stability depends on the insult](figures/fig05_stability.png)

*(a) The same tissue, two insults: retaining 30% of elastin, it adapts and
plateaus (blue); retaining only 3%, it dilates without bound (red). (b) The
stable/unstable map over the (surviving-elastin, pressure) plane, computed purely
from the equilibrated existence test. Mild insults live in the blue "adapts"
region; severe ones cross into the red "aneurysm" region.*

## 7.4 How the four theories answer

| Theory | Can it predict stability? | What it says |
|---|---|---|
| Kinematic growth | No — stability is *imposed* | Reaches the prescribed set-point, or runs away; you don't learn *why* from turnover. |
| Full CMM | Yes | Adapts or dilates depending on insult; the faithful reference. |
| Homogenized CMM | Yes | Same verdict as the full model, cheaply. |
| Equilibrated CMM | Existence, *instantly* | A root is *necessary* for adaptation; no root ⇒ unbounded growth. Gain-dependent dynamic stability is separate (§7.6). |

## 7.5 The takeaways of the whole lecture

1. **Kinematic growth** imposes a homeostatic target; it is simple and robust but
   cannot predict mechanobiological (in)stability.
2. **Constrained mixtures** predict stability from tissue turnover, and it
   **depends on the insult**.
3. The **homogenized** model reproduces the full model's trajectory at a fraction
   of the cost.
4. The **equilibrated** model matches the transient theories *when an equilibrium
   exists*, and — by failing to find one — flags when the wall lacks the *capacity*
   to adapt. Existence is **necessary but not sufficient**: reaching an equilibrium
   that exists also needs a strong enough adaptation gain (dynamic stability, §7.6).

---

### Exercise → [`exercises/ex05_stability_and_aneurysm.py`](../exercises/ex05_stability_and_aneurysm.py)

Reproduce the stability map, then explore what enlarges the *adapts* region:
stiffen the collagen (`--set model.constituents.collagen.law.c1=600`) or raise the
deposition stretch (`--set model.constituents.collagen.G=1.15`), and watch the
"aneurysm" region shrink. Raising the production **gain** leaves this map unchanged
— existence is gain-independent (see §7.6).

## 7.6 Existence is necessary; adaptation must also be *fast enough*

The map tests only whether an equilibrium **exists** — a capacity question set by
elastin, constituent stiffness, and deposition stretch. Whether the transient
actually *reaches* an equilibrium that exists is a separate, gain-dependent
question: the mechanobiological *dynamic* stability of Cyron & Humphrey (2014).
You can see it directly. Take an aneurysm *just inside* the existence boundary and
lower the gain in the transient (homogenized) model:

```bash
# elastin 12% is ABOVE the ~8% existence boundary, so an equilibrium EXISTS --
# yet with a weak gain the transient runs away (diverges); the default gain adapts:
uv run python run.py configs/ex02_constrained_mixture.yaml \
    --set theory=homogenized_cmm --set sweep.values="[1.0]" \
    --set insult.pressure_factor=1.0 --set insult.elastin_surviving=0.12 \
    --set insult.ramp=10 --set simulate.t_end=40000 \
    --set model.constituents.collagen.gain=0.1 --set model.constituents.smc.gain=0.1
```

Put both gains back to `1.0` and the same insult adapts. So the full statement is:
an equilibrium must **exist** (enough load-bearing capacity) **and** the adaptation
must be strong enough to **reach** it. (These reduced 1-D models capture the effect
only qualitatively — at very low gain the full and homogenized reductions can even
disagree — but the principle is real: stronger adaptation stabilises.)

# 1. The biology: why tissues grow and remodel

*Read this first. No equations here — just the biological picture that every model
in this repository is trying to capture.*

---

## 1.1 Living materials are never "finished"

An engineered steel beam is manufactured once and then slowly wears out. A living
artery is the opposite: it is **continuously torn down and rebuilt** throughout life.
The cells inside the wall constantly

- **deposit** new structural proteins, and
- **degrade** old ones,

while sensing the mechanical loads they carry. When the loads change, the cells change
*what* they build, *how much*, and *in what configuration*. Over weeks to months the
tissue's **mass, composition, and microstructure** are rewritten. We call the two
coupled processes:

- **Growth** — a change in *mass* (adding or removing material).
- **Remodeling** — a change in *microstructure / internal organization* (re-orienting
  fibers, changing their natural, unloaded length, swapping one constituent for another).

Together: **G&R**. The engineering payoff of understanding G&R is prediction — will this
hypertensive artery thicken and stabilize, or will this aneurysm keep dilating until it
ruptures?

---

## 1.2 The cast of characters in an arterial wall

The wall of a large artery is a fiber-reinforced soft composite. Three constituents
dominate its mechanics, and they could hardly be more different:

| Constituent | Made by | Mechanical role | Turnover in adults |
|---|---|---|---|
| **Elastin** | (mostly) laid down before birth | Soft, rubber-like, bears load at low stretch; stores elastic energy so the aorta recoils in diastole | **Essentially none** — half-life of *decades*. You keep the elastin you were born with. |
| **Collagen** | fibroblasts / smooth muscle cells | Stiff fibers, crimped at rest so they engage only at higher stretch; the main protection against overstretch and rupture | **Fast** — half-life of *weeks to months*. Constantly replaced. |
| **Smooth muscle (SMC)** | themselves | Bear passive load *and* actively contract to set vascular tone; also the main "sensor/builder" cells | Fast turnover; also change phenotype (contractile ↔ synthetic) |

Two facts from this table drive almost everything in the models:

1. **Elastin cannot be renewed.** If disease or age destroys it, it is gone for good.
   This is why elastin loss is the classic trigger for **aneurysm**.
2. **Collagen and SMC are in constant flux.** Because they are continuously produced and
   removed, the wall can *adapt* — but the same machinery, pushed too hard, can also
   *run away*.

---

## 1.3 Deposition pre-stretch: the key idea beginners miss

When a cell deposits a new collagen fiber into the loaded wall, it does **not** lay it
down slack. It cross-links the new fiber while the tissue is under load, so the fiber is
**born already stretched** — under tension — relative to its own natural (unloaded)
length. This built-in tension is the **deposition (pre-)stretch**, and it is roughly the
*same value every time*, because the cell is targeting a preferred mechanical state.

Consequence: each generation ("cohort") of fibers has its **own natural configuration**.
The wall is a mixture of constituents that do not share a common unloaded reference — a
**constrained mixture** (they are constrained to deform *together* in the current
configuration, but each remembers a different stress-free state). This single idea is
what separates constrained-mixture theory from classical continuum growth.

---

## 1.4 Mechanobiology: cells chase a mechanical set-point

Cells behave as if they are **regulating a target mechanical state** — a *homeostatic*
stress (or stretch) they "want" to feel. The governing intuition:

> If the stress a constituent carries is **above** its set-point, cells **build more** of
> it (and, for muscle, contract). If stress is **below** set-point, they build less and
> let removal win.

This negative feedback is what lets an artery under sustained **hypertension** thicken
its wall until the stress per unit material drops back to normal — *stress-mediated
adaptation*. Every model below is, at heart, a different mathematical hypothesis for
**how strongly and how quickly** the cells respond, and **what configuration** the new
material is deposited in.

---

## 1.5 Two canonical scenarios we will simulate

Throughout the exercises we drive the same tissue with two archetypal **insults** and
watch each theory respond:

- **Hypertension** — a sustained step increase in blood pressure. The healthy expectation
  is *adaptation*: the wall thickens and restores homeostatic stress. A good model should
  reproduce a stable return to a set-point.

- **Aneurysm (elastin loss)** — irreversible degradation of elastin. Now the load-bearing
  burden shifts onto collagen/SMC, and the geometry (radius, wall thinning) can feed back
  positively on stress. A good model must be able to predict **both** outcomes: a wall
  that stabilizes at a larger size, *or* one that dilates without bound (rupture).

The central scientific question of the whole lecture:

> **When does a tissue adapt to a stable new state, and when does it lose stability and
> run away?**

The four theories answer this question differently — and that is exactly what the code
lets you explore.

---

## 1.6 What each theory keeps and throws away (preview)

| Theory | Core idea | What it's good at | What it can't see |
|---|---|---|---|
| **Kinematic growth** | Postulate a stress-free "growth" deformation that drives stress to a set-point | Simple, robust, few parameters | No real mass turnover; stability is *assumed*, not predicted |
| **Constrained mixture (full)** | Track every cohort's mass and natural configuration via history integrals | Most faithful to biology; predicts (in)stability | Expensive; heavy bookkeeping (heredity integrals) |
| **Homogenized CMM** | Replace the whole history by *one* evolving mean configuration per constituent | Nearly as predictive, much cheaper; ODEs not integrals | Approximation of the full history |
| **Equilibrated CMM** | Skip the transient — solve directly for the final adapted state | Instant answer for the end state; clean stability test | **Only valid if a stable end state exists** |

The rest of the docs make each of these precise. Next: [finite-strain fundamentals](02_finite_strain.md).

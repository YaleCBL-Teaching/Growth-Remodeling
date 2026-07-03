# 2. Finite-strain fundamentals (the minimum you need)

*Goal: just enough continuum mechanics to read the four theories. If you have
seen finite strain before, skim to §2.4.*

---

## 2.1 Deformation and stretch

A body deforms from a **reference** configuration to a **current** one. The
deformation gradient $\mathbf{F}$ maps reference line elements to current ones.
Everything in this course collapses to a single dominant direction (the bar's
axis, or the artery's circumference), so we work with one scalar **stretch**

$$\lambda = \frac{\text{current length}}{\text{reference length}}.$$

$\lambda = 1$ is undeformed; $\lambda > 1$ is extension.

We assume the tissue is **incompressible** (it neither gains nor loses volume
elastically — only *growth* changes volume). That lets us recover the through-
thickness and transverse stretches from $\lambda$ alone, which is why one number
suffices.

## 2.2 Stress

We report the **Cauchy (true) stress** $\sigma$ — force per unit *current* area.
This is the physically meaningful one for a growing body, because the load-
bearing area itself changes as the tissue remodels. The Laplace law for a
pressurised thin tube (used for the artery) is naturally written in Cauchy
stress:

$$\sigma_\theta = \frac{P\,r}{h}\qquad\text{(circumferential wall stress)}$$

with pressure $P$, current inner radius $r$, wall thickness $h$.

The two settings, their boundary conditions, and the two insults are shown below.
The bar is loaded by a **dead axial load** $f$ (fixed at one end), so its required
stress grows like $\lambda^1$; the artery is loaded by **internal pressure** $P$,
so by Laplace its wall stress grows like $\lambda^2$. That single difference in
exponent is what makes the artery — but not the bar — able to lose stability
([§7](07_stability.md)).

![The shared setting: bar, artery, and the two insults](figures/fig00_setup.png)

*(a) The 1-D tissue bar under a dead load. (b) The thin-walled artery
cross-section: internal pressure $P$ (blue), circumferential wall stress
$\sigma_\theta$ (red), inner radius $r$, thickness $h$, balanced by Laplace. (c)
The two insults — hypertension raises $P$ (wall thickens); aneurysm degrades
elastin (the wall dilates, dashed = original size).*

## 2.3 Hyperelastic constituents

Each constituent stores energy in a strain-energy function and its stress is the
derivative. We use the two laws that describe arterial tissue (implemented in
[`gr/mechanics.py`](../src/gr/mechanics.py)):

**Elastin — neo-Hookean** (soft, barely stiffening; a rubber):

$$W_e = c_e\,(I_1 - 3),\qquad \sigma_e(\lambda_e) = c_e\!\left(\lambda_e^2 - \tfrac{1}{\lambda_e}\right).$$

**Collagen & smooth muscle — Fung exponential fiber** (crimped, then stiffens
steeply once recruited):

$$W = \frac{c_1}{4c_2}\Big(e^{\,c_2 (I_4-1)^2} - 1\Big),\qquad
\sigma(\lambda_e) = c_1\,\lambda_e^2\,(\lambda_e^2-1)\,e^{\,c_2(\lambda_e^2-1)^2},$$

where $I_4 = \lambda_e^2$ is the squared fiber stretch. These are exactly the
constituent free energies used in the constrained-mixture literature (e.g. the
FSGe formulation). The **material tangent** $\mathrm{d}\sigma/\mathrm{d}\lambda_e$
is also provided — we need it for equilibrium solves and for the stability
analysis in [§7](07_stability.md).

![Constituent laws and the bar-vs-artery feedback](figures/fig01_constitutive.png)

*Left: the three constituent stress–stretch laws, with the deposition stretch
$G^k$ and homeostatic stress $\sigma_h^k=\sigma^k(G^k)$ marked. Elastin is soft;
collagen and muscle stiffen. Right: the "required stress" that the loading
demands as a function of stretch — linear for the bar, **quadratic for the
artery** (Laplace). That extra power of $\lambda$ is the whole story of arterial
instability (§7).*

## 2.4 The deposition stretch $G^k$ (the crucial modelling idea)

Cells deposit new fibers **already under tension**, at a fixed **deposition
stretch** $G^k > 1$ (see [biology §1.3](01_biology.md)). So at homeostasis a
constituent's elastic stretch equals its own $G^k$, and we *define* its
homeostatic stress from that:

$$\boxed{\;\sigma_h^k := \sigma^k(G^k)\;}\tag{2.1}$$

This one convention (coded in [`gr/parameters.py`](../src/gr/parameters.py)) pins
down every set-point in the course from a few physical inputs, and is why all
four theories can share parameters.

## 2.5 Multiplicative decomposition — growth vs. elasticity

The single most important kinematic idea in G&R: split the deformation into a
stress-free **inelastic** part (growth/remodeling) and an **elastic** part (the
only part that carries stress). In 1D,

$$\lambda = \lambda_e \,\lambda_{\text{inel}}.\tag{2.2}$$

- **Kinematic growth** ([§3](03_kinematic_growth.md)) uses one such split with an
  inelastic *growth* stretch.
- **Constrained mixtures** ([§4](04_constrained_mixture.md)) give *each cohort of
  each constituent* its own inelastic natural configuration and superpose them.

Equation (2.2) and the set-point (2.1) are the two pieces of machinery you will
see reused in every model. Next: [kinematic growth](03_kinematic_growth.md).

r"""
gr — a teaching package comparing four growth-and-remodeling (G&R) theories for
soft tissue.

Layout (see the repository README):
  * FUNDAMENTALS (this package)  -- the maths and models; read, don't edit.
  * exercises/                   -- student files; change parameters and run.
  * solutions/                   -- teacher files; generate the lecture figures.

The four theories, each a ``simulate(...)`` (or ``solve(...)``) taking a shared
:class:`~gr.geometry.Geometry` and :class:`~gr.parameters.Insult`:

    from gr import bar, artery, Model, Insult, HYPERTENSION, ANEURYSM
    from gr import kinematic_growth, constrained_mixture, homogenized_cmm, equilibrated_cmm

    model = Model()
    art = artery(model)
    res = homogenized_cmm.simulate(art, HYPERTENSION)
"""
from __future__ import annotations

from . import (
    constrained_mixture,
    equilibrated_cmm,
    homogenized_cmm,
    kinematic_growth,
)
from .geometry import Geometry, artery, bar
from .history import Result
from .parameters import (
    ANEURYSM,
    HYPERTENSION,
    Constituent,
    Insult,
    Model,
    default_constituents,
)

__all__ = [
    "Model",
    "Constituent",
    "Insult",
    "HYPERTENSION",
    "ANEURYSM",
    "default_constituents",
    "Geometry",
    "bar",
    "artery",
    "Result",
    "kinematic_growth",
    "constrained_mixture",
    "homogenized_cmm",
    "equilibrated_cmm",
]

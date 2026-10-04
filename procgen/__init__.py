"""Hybrid procedural plant graphics — sine where it helps, shapes where it doesn't."""

from procgen.morph import (
    MorphParams,
    demo_catalog,
    morph_from_phenotype,
    morph_from_traits,
    seed_from_plant_id,
)
from procgen.preview import render_gallery, render_plant_card

__all__ = [
    "MorphParams",
    "demo_catalog",
    "morph_from_phenotype",
    "morph_from_traits",
    "seed_from_plant_id",
    "render_gallery",
    "render_plant_card",
]

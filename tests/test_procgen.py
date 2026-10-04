"""Tests for hybrid sine morph renderer and phenotype bridge."""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random

import pygame
import pytest

from genetics.plant import breed, create_seed_plant
from procgen.morph import (
    morph_from_phenotype,
    morph_from_traits,
    seed_from_plant_id,
)
from procgen.plant_scene import build_scene
from procgen.waves import harmonic_offset, sample_stem_curve
from ui.plant_renderer import draw_plant, plant_portrait


def test_harmonic_offset_zero_at_origin_phase():
    assert abs(harmonic_offset(0.0, amp=1.0, freq=1.0, phase=0.0)) < 1e-9


def test_stem_curve_grows_upward():
    pts = sample_stem_curve(length=100, amp=10, freq=1.2, phase=0.3, steps=20)
    assert pts[0][1] == 0
    assert pts[-1][1] < pts[0][1]
    assert len(pts) == 21


def test_seed_from_plant_id_stable():
    assert seed_from_plant_id("abc") == seed_from_plant_id("abc")
    assert seed_from_plant_id("abc") != seed_from_plant_id("abd")


def test_morph_from_phenotype_maps_mutations():
    rng = random.Random(7)
    plant = create_seed_plant("Test", rng=rng, quality="exotic")
    # Force spiral mutant alleles if locus present
    key = "mut_spiral_growth"
    if key in plant.genotype:
        plant.genotype[key] = ("mut", "mut")
        plant._phenotype = None
    ph = plant.phenotype()
    morph = morph_from_phenotype(ph, seed=seed_from_plant_id(plant.id), label=plant.name)
    assert morph.height == pytest.approx(ph.height)
    assert morph.colour == tuple(ph.colour_rgb)
    if "spiral_growth" in ph.expressed_mutations:
        assert morph.spiral is True


def test_build_scene_has_stem_geometry():
    morph = morph_from_traits("Demo", height=0.8, seed=3, mutations=["spiral_growth"])
    scene = build_scene(morph, (100, 200), 120, time_s=0.2)
    assert scene.polylines
    assert scene.draw_pot is True


def test_draw_plant_and_portrait():
    pygame.init()
    rng = random.Random(99)
    a = create_seed_plant("A", rng=rng, quality="premium")
    a.mature = True
    a.growth_progress = 1.0
    surf = pygame.Surface((200, 200))
    draw_plant(surf, a, (100, 180), 100, time_s=0.5)
    portrait = plant_portrait(a, size=120, time_s=0.5)
    assert portrait.get_width() == 120


def test_breeding_offspring_morph_related():
    rng = random.Random(123)
    a = create_seed_plant("ParentA", rng=rng, quality="premium")
    b = create_seed_plant("ParentB", rng=rng, quality="premium")
    a.mature = b.mature = True
    child = breed(a, b, "Kid", rng=rng)
    ma = morph_from_phenotype(a.phenotype(), seed=seed_from_plant_id(a.id))
    mb = morph_from_phenotype(b.phenotype(), seed=seed_from_plant_id(b.id))
    mc = morph_from_phenotype(child.phenotype(), seed=seed_from_plant_id(child.id))
    # Offspring height sits between a broad parental band (soft check)
    lo = min(ma.height, mb.height) - 0.35
    hi = max(ma.height, mb.height) + 0.35
    assert lo <= mc.height <= hi
    # Seeds differ so phase/layout variation exists
    assert ma.seed != mc.seed or mb.seed != mc.seed

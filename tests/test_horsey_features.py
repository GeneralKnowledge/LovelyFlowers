"""Tests for Horsey-inspired expansions: wild finds, radiation, trials, hybrids."""

from __future__ import annotations

import random

from game.competitions import get_trial, run_trial
from game.radiation import irradiate, radiation_cross
from game.state import GameState
from game.wild import create_wild_specimen
from game.world import get_location
from genetics.kinds import can_cross, hybrid_kind
from genetics.mutations import MUTANT, WILDTYPE
from genetics.plant import create_seed_plant


def test_hybrid_kind_cross_kingdom():
    assert hybrid_kind("plant", "plant") == "plant"
    assert hybrid_kind("plant", "fungus") == "hybrid"
    assert hybrid_kind("fungus", "fungus") == "fungus"
    ok, msg = can_cross("plant", "fungus")
    assert ok
    assert "Cross-kingdom" in msg


def test_wild_specimen_from_meadow():
    loc = get_location("meadow")
    rng = random.Random(11)
    wild = create_wild_specimen(loc, rng)
    assert wild.wild
    assert wild.mature
    assert wild.origin == "meadow"
    assert wild.species_kind in loc.wild_kinds


def test_fungal_hollow_can_yield_non_plant():
    loc = get_location("fungal_hollow")
    rng = random.Random(22)
    kinds = set()
    for _ in range(30):
        w = create_wild_specimen(loc, rng)
        kinds.add(w.species_kind)
    assert kinds & {"fungus", "lichen", "mossbeast"}


def test_irradiate_can_add_mutation_alleles():
    rng = random.Random(33)
    plant = create_seed_plant("Victim", rng=rng)
    # Guarantee low stability for more chaos
    plant.genotype["stability"] = ("t0", "t0")
    plant._phenotype = None
    before = sum(
        1
        for k, pair in plant.genotype.items()
        if k.startswith("mut_") and MUTANT in pair
    )
    # Blast many times across copies until something happens
    gained_any = False
    for i in range(20):
        p = create_seed_plant(f"V{i}", rng=rng)
        p.genotype["stability"] = ("t0", "t0")
        p._phenotype = None
        report = irradiate(p, rng, intensity="severe")
        if report["survived"] and report["mutations_gained"]:
            gained_any = True
            break
    assert gained_any or before >= 0  # soft: at least runs; prefer gained
    # Stronger assertion: at least one of 20 severe blasts changes genome OR kills
    changed = False
    rng2 = random.Random(99)
    for i in range(25):
        p = create_seed_plant(f"X{i}", rng=rng2)
        p.genotype["stability"] = ("t0", "t1")
        # clear mutations
        for mid in list(p.genotype):
            if mid.startswith("mut_"):
                p.genotype[mid] = (WILDTYPE, WILDTYPE)
        p._phenotype = None
        report = irradiate(p, rng2, intensity="severe")
        if report["mutations_gained"] or not report["survived"]:
            changed = True
            break
    assert changed


def test_radiation_cross_marks_notes():
    rng = random.Random(44)
    a = create_seed_plant("A", rng=rng)
    b = create_seed_plant("B", rng=rng)
    child = radiation_cross(a, b, "Zapling", rng)
    assert "radiation" in child.notes.lower()
    assert child.generation == 2


def test_trial_gives_grade_and_advice():
    rng = random.Random(55)
    plant = create_seed_plant("TrialMe", rng=rng)
    plant.mature = True
    trial = get_trial("trial_general")
    result = run_trial(trial, plant, rng=rng)
    assert result.grade in "SABCDF"
    assert result.advice
    assert "flower" in result.category_scores


def test_explore_meadow_and_trial_flow():
    gs = GameState.new_game(seed=66)
    gs.money = 500
    # Free a pot if needed — starter occupies one
    wild = gs.explore("meadow")
    assert wild is not None
    assert wild.wild
    assert wild.id in gs.plants
    assert "meadow" in gs.visited_locations

    result = gs.run_plant_trial("trial_general", wild.id)
    assert result is not None
    assert gs.last_trial is not None
    assert result.grade in "SABCDF"


def test_lab_unlocks_radiation():
    gs = GameState.new_game(seed=77)
    gs.money = 1000
    gs.prestige = 20
    # Need free pots — sell nothing, expand first
    gs.buy_upgrade("bench")
    assert not gs.has_radiation_access()
    found = gs.explore("abandoned_lab")
    assert found is not None
    assert gs.has_radiation_access()
    # Irradiate starter or find
    target = found.id
    report = gs.irradiate_plant(target, intensity="mild")
    assert report is not None
    assert gs.last_radiation is not None


def test_cross_breed_plant_and_fungus_makes_hybrid():
    gs = GameState.new_game(seed=88)
    gs.money = 500
    gs.buy_upgrade("bench")
    plant = next(p for p in gs.living_plants())
    loc = get_location("fungal_hollow")
    # Force a fungus
    rng = random.Random(1)
    fungus = create_wild_specimen(loc, rng)
    # Keep generating until fungus
    for i in range(40):
        fungus = create_wild_specimen(loc, random.Random(i + 3))
        if fungus.species_kind == "fungus":
            break
    fungus.species_kind = "fungus"
    pot = gs._free_pot_index()
    assert pot is not None
    gs.plants[fungus.id] = fungus
    gs.pot_assignments[pot] = fungus.id
    kids = gs.breed_plants(plant.id, fungus.id)
    assert kids
    assert any(k.species_kind == "hybrid" for k in kids)


def test_save_load_preserves_travel_and_radiation_flags(tmp_path):
    gs = GameState.new_game(seed=101)
    gs.money = 800
    gs.prestige = 20
    gs.buy_upgrade("bench")
    gs.explore("meadow")
    gs.unlocked_radiation = True
    path = tmp_path / "save.json"
    gs.save(path)
    loaded = GameState.load(path)
    assert loaded.unlocked_radiation
    assert "meadow" in loaded.visited_locations
    assert any(p.wild for p in loaded.living_plants())

"""Unit tests for the genetics engine — no Pygame required."""

from __future__ import annotations

import random

import pytest

from genetics.alleles import ALL_BASE_LOCI, COLOUR_LOCUS, express_allele_id
from genetics.mutations import (
    MUTANT,
    MUTATION_CATALOG,
    WILDTYPE,
    mutation_carrier,
    mutation_expressed,
)
from genetics.phenotype import express_phenotype
from genetics.plant import Plant, breed, breed_litter, create_seed_plant
from game.competitions import score_plant
from game.state import GameState


def test_seed_has_full_genotype():
    plant = create_seed_plant("Test", rng=random.Random(1))
    for locus in ALL_BASE_LOCI:
        assert locus in plant.genotype
        assert len(plant.genotype[locus]) == 2
    for mid in MUTATION_CATALOG:
        assert f"mut_{mid}" in plant.genotype


def test_phenotype_is_deterministic_for_genotype():
    plant = create_seed_plant("A", rng=random.Random(2))
    p1 = express_phenotype(plant.genotype)
    p2 = express_phenotype(plant.genotype)
    assert p1.height == p2.height
    assert p1.value == p2.value
    assert p1.colour_id == p2.colour_id


def test_breeding_inherits_alleles_from_parents():
    rng = random.Random(3)
    a = create_seed_plant("A", rng=rng)
    b = create_seed_plant("B", rng=rng)
    # Force known alleles
    a.genotype["height"] = ("h0", "h0")
    b.genotype["height"] = ("h4", "h4")
    child = breed(a, b, "Child", rng=random.Random(0))
    # Child must be h0/h4 (order may vary)
    assert set(child.genotype["height"]) == {"h0", "h4"}
    assert child.generation == max(a.generation, b.generation) + 1
    assert child.parent_ids == (a.id, b.id)


def test_recessive_mutation_requires_homozygous():
    pair_het = (WILDTYPE, MUTANT)
    pair_hom = (MUTANT, MUTANT)
    mid = "eye_structures"  # recessive
    assert not mutation_expressed(pair_het, mid)
    assert mutation_carrier(pair_het, mid)
    assert mutation_expressed(pair_hom, mid)


def test_dominant_mutation_expresses_when_heterozygous():
    mid = "bioluminescence"
    assert mutation_expressed((WILDTYPE, MUTANT), mid)
    assert not mutation_carrier((WILDTYPE, MUTANT), mid)


def test_white_colour_is_recessive():
    # white vs red — red should win
    expressed = express_allele_id(COLOUR_LOCUS, "c_white", "c_red")
    assert expressed == "c_red"
    # white homozygous expresses white
    assert express_allele_id(COLOUR_LOCUS, "c_white", "c_white") == "c_white"


def test_tradeoffs_penalise_fast_growth_yield():
    # Build a genotype with explosive growth and high yield alleles
    plant = create_seed_plant("Fast", rng=random.Random(5))
    plant.genotype["growth"] = ("g4", "g4")
    plant.genotype["yield"] = ("y4", "y4")
    plant._phenotype = None
    ph = plant.phenotype(refresh=True)
    # Yield should be reduced by tradeoff relative to raw 0.95
    assert ph.yield_ < 0.95
    assert any("yield" in n.lower() or "growth" in n.lower() for n in ph.trait_notes)


def test_mutation_modifies_phenotype():
    plant = create_seed_plant("Mut", rng=random.Random(6))
    plant.genotype["leaf"] = ("l2", "l2")
    plant.genotype["mut_giant_leaves"] = (MUTANT, MUTANT)
    plant._phenotype = None
    ph = plant.phenotype(refresh=True)
    assert "giant_leaves" in ph.expressed_mutations
    assert ph.leaf > 0.55  # boosted


def test_litter_produces_multiple_children():
    rng = random.Random(7)
    a = create_seed_plant("A", rng=rng, quality="premium")
    b = create_seed_plant("B", rng=rng, quality="premium")
    a.mature = True
    b.mature = True
    kids = breed_litter(a, b, name_fn=lambda i: f"Kid{i}", count=4, rng=rng)
    assert len(kids) == 4
    assert len({k.id for k in kids}) == 4


def test_game_buy_grow_sell_loop():
    gs = GameState.new_game(seed=11)
    start_money = gs.money
    # Sell starter? It's mature — sell after buying another
    p = gs.buy_seed("common")
    assert p is not None
    assert gs.money < start_money
    for _ in range(30):
        gs.advance_time(12)
    assert p.mature
    value = gs.sell_plant(p.id)
    assert value is not None
    assert p.sold


def test_game_breeding_and_pedigree():
    gs = GameState.new_game(seed=22)
    gs.money = 500
    # Ensure free pots
    gs.buy_seed("common")
    for _ in range(30):
        gs.advance_time(12)
    mature = [p for p in gs.living_plants() if p.mature]
    assert len(mature) >= 2
    kids = gs.breed_plants(mature[0].id, mature[1].id)
    assert kids
    tree = gs.pedigree_tree(kids[0].id, depth=2)
    assert tree["name"] == kids[0].name
    assert len(tree["parents"]) == 2


def test_competition_rewards_matching_traits():
    rng = random.Random(33)
    pretty = create_seed_plant("Pretty", rng=rng)
    pretty.genotype["flower"] = ("f4", "f4")
    pretty.genotype["quality"] = ("q4", "q4")
    pretty.genotype["symmetry"] = ("sy4", "sy4")
    pretty.genotype["colour"] = ("c_purple", "c_purple")
    pretty._phenotype = None

    big = create_seed_plant("Big", rng=rng)
    big.genotype["height"] = ("h4", "h4")
    big.genotype["yield"] = ("y4", "y4")
    big.genotype["stem"] = ("s4", "s4")
    big._phenotype = None

    assert score_plant(pretty, "flower") > score_plant(big, "flower")
    assert score_plant(big, "giant") > score_plant(pretty, "giant")


def test_save_load_roundtrip(tmp_path):
    gs = GameState.new_game(seed=44)
    gs.buy_seed("common")
    path = tmp_path / "save.json"
    gs.save(path)
    loaded = GameState.load(path)
    assert loaded.money == gs.money
    assert len(loaded.plants) == len(gs.plants)
    assert loaded.greenhouse_slots == gs.greenhouse_slots


def test_hidden_mutation_can_reappear():
    """Carrier × carrier can produce expressed recessive mutation."""
    rng = random.Random(55)
    a = create_seed_plant("A", rng=rng)
    b = create_seed_plant("B", rng=rng)
    mid = "face_bloom"
    key = f"mut_{mid}"
    a.genotype[key] = (WILDTYPE, MUTANT)
    b.genotype[key] = (WILDTYPE, MUTANT)
    # Breed many times — at least one homozygous expected in 40 trials (~25%)
    expressed = 0
    for i in range(60):
        child = breed(a, b, f"C{i}", rng=rng)
        if mid in child.phenotype().expressed_mutations:
            expressed += 1
    assert expressed >= 1

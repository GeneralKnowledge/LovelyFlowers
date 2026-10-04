"""Wild specimen generation and weird non-plant kinds."""

from __future__ import annotations

import random
from typing import Optional

from game.names import random_name
from game.world import KIND_HUMOUR, Location
from genetics.kinds import KIND_LABELS
from genetics.mutations import MUTANT, MUTATION_CATALOG, WILDTYPE
from genetics.plant import Plant, create_seed_plant

__all__ = ["create_wild_specimen", "KIND_LABELS"]


WILD_NAME_PREFIX = {
    "plant": ["Wild", "Stray", "Roadside", "Hedgerow"],
    "fungus": ["Cap", "Spore", "Bracket", "Puff"],
    "lichen": ["Crust", "Ruffle", "Map"],
    "mossbeast": ["Tuft", "Carpet", "Lumber"],
    "bloomcritter": ["Petal", "Buzz", "Wander"],
    "hybrid": ["Chimera", "Oops", "Merge"],
}


def create_wild_specimen(
    location: Location,
    rng: random.Random,
    used_names: Optional[set] = None,
) -> Plant:
    """Generate a wild find from a location — may be a non-plant."""
    kind = rng.choice(location.wild_kinds)
    quality = location.wild_quality
    if quality == "volatile":
        base_quality = rng.choice(["premium", "exotic", "exotic"])
    elif quality in ("common", "premium", "exotic"):
        base_quality = quality
    else:
        base_quality = "exotic"

    plant = create_seed_plant(
        _wild_name(kind, rng, used_names),
        rng=rng,
        quality=base_quality,
    )
    plant.species_kind = kind
    plant.origin = location.id
    plant.wild = True
    plant.mature = True
    plant.planted = True
    plant.growth_progress = 1.0
    plant.age_days = plant.phenotype().maturity_days
    plant.notes = KIND_HUMOUR.get(kind, "")

    _apply_mutation_bias(plant, location.mutation_bias, rng)

    if kind == "fungus":
        plant.genotype["leaf"] = ("l0", "l1")
        plant.genotype["flower"] = ("f0", rng.choice(["f0", "f1", "f2"]))
        plant.genotype["stem"] = ("s1", "s2")
    elif kind == "mossbeast":
        plant.genotype["height"] = ("h0", "h1")
        plant.genotype["width"] = ("w3", "w4")
        plant.genotype["branch"] = ("b3", "b4")
    elif kind == "bloomcritter":
        plant.genotype["growth"] = ("g3", "g4")
        plant.genotype["flower"] = ("f3", "f4")
        key = "mut_walking_roots"
        if rng.random() < 0.35:
            plant.genotype[key] = (
                (WILDTYPE, MUTANT) if rng.random() < 0.6 else (MUTANT, MUTANT)
            )

    plant._phenotype = None
    plant.phenotype(refresh=True)
    return plant


def _wild_name(kind: str, rng: random.Random, used: Optional[set]) -> str:
    prefix = rng.choice(WILD_NAME_PREFIX.get(kind, ["Wild"]))
    base = random_name(rng, used)
    first = base.split()[0]
    return f"{prefix} {first}"


def _apply_mutation_bias(plant: Plant, bias: float, rng: random.Random) -> None:
    if bias <= 0:
        return
    for mid, mut in MUTATION_CATALOG.items():
        key = f"mut_{mid}"
        if rng.random() < bias * (0.5 + mut.rarity * 8):
            if rng.random() < 0.25:
                plant.genotype[key] = (MUTANT, MUTANT)
            else:
                plant.genotype[key] = (WILDTYPE, MUTANT)

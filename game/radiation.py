"""Radiation chamber — forced mutation and volatile experimental crosses."""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

from genetics.mutations import MUTANT, MUTATION_CATALOG, WILDTYPE
from genetics.plant import Plant, breed


RADIATION_COST = 25
RADIATION_HOURS = 6.0


def irradiate(
    plant: Plant,
    rng: random.Random,
    intensity: str = "standard",
) -> Dict:
    """
    Expose a specimen to radiation.
    Returns a report dict: mutations_gained, mutations_lost, notes, survived.
    Modifies plant genotype in place.
    """
    mult = {"mild": 0.6, "standard": 1.0, "severe": 1.7}.get(intensity, 1.0)
    gained: List[str] = []
    lost: List[str] = []
    notes: List[str] = []

    # Stability resists chaos; low stability = more events
    stability = plant.phenotype().stability
    chaos = max(0.2, (1.15 - stability) * mult)

    # Chance to die / severely damage under severe radiation
    if intensity == "severe" and rng.random() < 0.08 * chaos:
        notes.append("The specimen collapsed into compost. Catastrophically.")
        return {
            "survived": False,
            "mutations_gained": [],
            "mutations_lost": [],
            "notes": notes,
            "intensity": intensity,
        }

    for mid, mut in MUTATION_CATALOG.items():
        key = f"mut_{mid}"
        pair = list(plant.genotype.get(key, (WILDTYPE, WILDTYPE)))
        rate = mut.rarity * 4.5 * chaos  # much higher than natural breeding
        if pair.count(MUTANT) < 2 and rng.random() < rate:
            for i, al in enumerate(pair):
                if al == WILDTYPE:
                    pair[i] = MUTANT
                    break
            plant.genotype[key] = (pair[0], pair[1])
            gained.append(mid)
        elif pair.count(MUTANT) > 0 and rng.random() < 0.04 * chaos:
            for i, al in enumerate(pair):
                if al == MUTANT:
                    pair[i] = WILDTYPE
                    break
            plant.genotype[key] = (pair[0], pair[1])
            lost.append(mid)

    # Stability allele jitter — radiation scars the genome
    if "stability" in plant.genotype and rng.random() < 0.55 * mult:
        a, b = plant.genotype["stability"]
        # Nudge toward lower stability alleles when possible
        alleles = ["t0", "t1", "t2", "t3", "t4"]
        def nudge(x: str) -> str:
            if x not in alleles:
                return x
            idx = alleles.index(x)
            return alleles[max(0, idx - 1)] if rng.random() < 0.7 else x
        plant.genotype["stability"] = (nudge(a), nudge(b))
        notes.append("Genetic stability took a hit.")

    # Random quantitative jitter under severe
    if intensity == "severe":
        for locus in ("height", "growth", "flower", "yield", "stem"):
            if locus not in plant.genotype:
                continue
            if rng.random() < 0.35:
                a, b = plant.genotype[locus]
                # Swap one allele randomly within same locus by string mutation-ish:
                # keep allele but flip order — mild; better: pick neighbor id
                plant.genotype[locus] = (b, a)
                notes.append(f"{locus.title()} alleles scrambled.")

    plant._phenotype = None  # refresh cache
    plant.phenotype(refresh=True)

    if gained:
        notes.append("Radiation cooked new alleles into existence.")
    elif not lost:
        notes.append("Nothing obvious changed. The Geiger counter disagrees.")

    return {
        "survived": True,
        "mutations_gained": gained,
        "mutations_lost": lost,
        "notes": notes,
        "intensity": intensity,
    }


def radiation_cross(
    parent_a: Plant,
    parent_b: Plant,
    name: str,
    rng: random.Random,
) -> Plant:
    """
    Breed under radiation — inheritance plus guaranteed mutation pressure.
    Used at Radiation Flats or in the chamber for experimental crosses.
    """
    child = breed(parent_a, parent_b, name, rng=rng)
    # Extra forced mutation attempts on the offspring
    irradiate(child, rng, intensity="mild")
    child.notes = (child.notes + " Born under radiation.").strip()
    return child

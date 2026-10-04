"""Humorous plant naming — bloodlines, epithets, and greenhouse nicknames."""

from __future__ import annotations

import random
from typing import List, Optional

from genetics.mutations import MUTATION_CATALOG
from genetics.plant import Plant


FIRST_NAMES = [
    "Mavis", "Kevin", "Brenda", "Nigel", "Doris", "Gerald", "Peggy", "Clive",
    "Mildred", "Barry", "Enid", "Trevor", "Agnes", "Rupert", "Hilda", "Colin",
    "Vera", "Derek", "Muriel", "Stanley", "Edna", "Norman", "Gladys", "Keith",
    "Petunia", "Basil", "Ivy", "Fern", "Moss", "Clover", "Thistle", "Briar",
    "Willow", "Juniper", "Poppy", "Hazel", "Maple", "Ash", "Rowan", "Olive",
]

EPITHETS = [
    "the Mild", "the Unwise", "the Promising", "the Awkward", "the Dense",
    "the Speedy", "the Stout", "the Peculiar", "the Gleaming", "the Crooked",
    "the Proud", "the Doubtful", "the Legendary", "the Accidental",
    "the Overachiever", "the Mistake", "the Masterpiece",
]

BLOODLINE_TITLES = [
    "Beast", "Empress", "Oddity", "Titan", "Whisper", "Catastrophe",
    "Jewel", "Menace", "Darling", "Abomination", "Marvel", "Horror",
]


def random_name(rng: random.Random, used: Optional[set] = None) -> str:
    used = used or set()
    for _ in range(40):
        name = rng.choice(FIRST_NAMES)
        if rng.random() < 0.25:
            name = f"{name} {rng.choice(EPITHETS)}"
        if name not in used:
            return name
    return f"{rng.choice(FIRST_NAMES)}-{rng.randint(100, 999)}"


def next_in_line(parent_name: str, generation: int, rng: random.Random) -> str:
    """Continue a bloodline name: Mavis → Mavis II → Mavis III, or crown a Beast."""
    base = parent_name
    # Strip existing roman numerals / epithets for chaining
    for epi in EPITHETS:
        if base.endswith(epi):
            base = base[: -len(epi)].strip()
    # Strip trailing roman numerals
    parts = base.split()
    if parts and _is_roman(parts[-1]):
        base = " ".join(parts[:-1])

    if generation >= 7 and rng.random() < 0.35:
        title = rng.choice(BLOODLINE_TITLES)
        numeral = _to_roman(max(1, generation - 6))
        return f"The {title} {numeral}".strip()

    numeral = _to_roman(max(2, min(generation, 20)))
    return f"{base} {numeral}"


def offspring_names(
    parent_a: Plant,
    parent_b: Plant,
    count: int,
    rng: random.Random,
    used: Optional[set] = None,
) -> List[str]:
    used = used or set()
    names = []
    # Prefer continuing the higher-generation / more mutated parent's line
    primary = parent_a if parent_a.generation >= parent_b.generation else parent_b
    if len(parent_a.phenotype().expressed_mutations) > len(parent_b.phenotype().expressed_mutations):
        primary = parent_a
    elif len(parent_b.phenotype().expressed_mutations) > len(parent_a.phenotype().expressed_mutations):
        primary = parent_b

    for i in range(count):
        if i == 0 and rng.random() < 0.55:
            name = next_in_line(primary.name, max(parent_a.generation, parent_b.generation) + 1, rng)
        elif rng.random() < 0.3:
            name = next_in_line(
                parent_b.name if primary is parent_a else parent_a.name,
                max(parent_a.generation, parent_b.generation) + 1,
                rng,
            )
        else:
            name = random_name(rng, used)
        # Ensure uniqueness
        original = name
        n = 2
        while name in used or name in names:
            name = f"{original}-{n}"
            n += 1
        names.append(name)
    return names


def humorous_description(plant: Plant) -> str:
    ph = plant.phenotype()
    bits = []
    kind = getattr(plant, "species_kind", "plant")
    if kind == "fungus":
        bits.append("Insists it is not a plant. The greenhouse disagrees.")
    elif kind == "mossbeast":
        bits.append("Moss with ambition and poor boundaries.")
    elif kind == "bloomcritter":
        bits.append("Floral. Possibly fleeing.")
    elif kind == "hybrid":
        bits.append("Taxonomy has filed a missing-person report.")
    elif kind == "lichen":
        bits.append("A committee wearing one coat.")
    if ph.height > 0.8:
        bits.append("Looms like it pays rent.")
    elif ph.height < 0.3 and kind == "plant":
        bits.append("Could lose a staring contest with a mushroom.")
    if ph.growth > 0.8:
        bits.append("Grows with concerning enthusiasm.")
    if ph.flower > 0.8:
        bits.append("More flower than plant, frankly.")
    if ph.stem < 0.35:
        bits.append("Structurally optimistic.")
    if ph.yield_ > 0.8:
        bits.append("Produces like it's showing off.")
    if getattr(plant, "wild", False):
        bits.append("Dragged in from the wild. Still sulking.")
    if getattr(plant, "irradiated", False):
        bits.append("Smells faintly of ozone and poor decisions.")
    for mid in ph.expressed_mutations:
        bits.append(MUTATION_CATALOG[mid].humour)
    if not bits:
        bits.append("A respectable specimen. Dangerous words in this greenhouse.")
    if plant.generation >= 10:
        bits.append(f"Generation {plant.generation}. The lineage has opinions.")
    return " ".join(bits[:3])


def _is_roman(s: str) -> bool:
    return bool(s) and all(c in "IVXLCDM" for c in s.upper()) and s.upper() == s


def _to_roman(n: int) -> str:
    vals = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    n = max(1, min(n, 39))
    out = []
    for v, sym in vals:
        while n >= v:
            out.append(sym)
            n -= v
    return "".join(out)

"""Mutation catalog — genes that can appear, hide, and reappear across generations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from genetics.alleles import Allele, Dominance, Locus


@dataclass(frozen=True)
class MutationDef:
    """Definition of a heritable botanical mutation."""

    id: str
    name: str
    description: str
    rarity: float  # spontaneous chance weight (lower = rarer)
    mode: Dominance
    # Phenotype multipliers applied when expressed
    trait_mods: Dict[str, float]
    # Competition category bonuses when expressed
    contest_bonus: Dict[str, float]
    humour: str
    discovery_hint: str


MUTATION_CATALOG: Dict[str, MutationDef] = {
    "giant_leaves": MutationDef(
        id="giant_leaves",
        name="Giant Leaves",
        description="Leaves inflate to improbable parasols.",
        rarity=0.04,
        mode=Dominance.RECESSIVE_MUTATION,
        trait_mods={"leaf": 1.45, "water": 0.85, "growth": 0.9},
        contest_bonus={"giant": 8, "abomination": 4},
        humour="It casts a shadow large enough to picnic under.",
        discovery_hint="Huge foliage blotting out neighbouring pots.",
    ),
    "spiral_growth": MutationDef(
        id="spiral_growth",
        name="Spiral Growth",
        description="The stem corkscrews skyward like a botanical drill.",
        rarity=0.035,
        mode=Dominance.RECESSIVE_MUTATION,
        trait_mods={"height": 1.15, "symmetry": 0.7, "stem": 0.9},
        contest_bonus={"abomination": 10, "flower": 3},
        humour="Gardeners get dizzy watering it.",
        discovery_hint="A corkscrew silhouette that refuses to stand straight.",
    ),
    "dense_bloom": MutationDef(
        id="dense_bloom",
        name="Extremely Dense Flowers",
        description="Blooms pack so tight the plant looks upholstered.",
        rarity=0.045,
        mode=Dominance.INCOMPLETE,
        trait_mods={"flower": 1.5, "yield": 1.25, "disease": 0.75},
        contest_bonus={"flower": 12, "people": 4},
        humour="Bees need a reservation.",
        discovery_hint="Petals stacked like a floral traffic jam.",
    ),
    "bioluminescence": MutationDef(
        id="bioluminescence",
        name="Bioluminescent Flowers",
        description="Petals glow softly after dusk — and in poorly lit greenhouses.",
        rarity=0.02,
        mode=Dominance.DOMINANT_MUTATION,
        trait_mods={"quality": 1.2, "flower": 1.1},
        contest_bonus={"flower": 8, "abomination": 10, "people": 6},
        humour="Handy as a night-light. Terrible for stealth gardening.",
        discovery_hint="An eerie glow that shouldn't come from chlorophyll.",
    ),
    "feather_leaves": MutationDef(
        id="feather_leaves",
        name="Feather-like Leaves",
        description="Foliage frays into soft, plumage-like fronds.",
        rarity=0.03,
        mode=Dominance.RECESSIVE_MUTATION,
        trait_mods={"leaf": 1.2, "water": 0.9, "quality": 1.15},
        contest_bonus={"flower": 5, "abomination": 8, "people": 5},
        humour="Birds keep trying to nest in it. The plant is offended.",
        discovery_hint="Leaves that look ready to molt.",
    ),
    "eye_structures": MutationDef(
        id="eye_structures",
        name="Eye-like Structures",
        description="Flower centres develop uncanny ocular patterns.",
        rarity=0.015,
        mode=Dominance.RECESSIVE_MUTATION,
        trait_mods={"flower": 1.1, "quality": 1.05, "symmetry": 0.85},
        contest_bonus={"abomination": 18, "people": 8},
        humour="It is not staring at you. It is staring through you.",
        discovery_hint="Blooms that blink when you're not looking. Allegedly.",
    ),
    "walking_roots": MutationDef(
        id="walking_roots",
        name="Leg-like Roots",
        description="Root masses thicken into stubby ambulatory limbs.",
        rarity=0.012,
        mode=Dominance.RECESSIVE_MUTATION,
        trait_mods={"water": 1.2, "growth": 0.85, "stem": 1.1},
        contest_bonus={"abomination": 20, "speed": 4, "people": 6},
        humour="It has not walked away. Yet. You check twice nightly.",
        discovery_hint="Roots that look like they filed a travel itinerary.",
    ),
    "face_bloom": MutationDef(
        id="face_bloom",
        name="Face-like Flowers",
        description="Petal arrangement forms a vaguely judgmental face.",
        rarity=0.01,
        mode=Dominance.RECESSIVE_MUTATION,
        trait_mods={"flower": 1.15, "quality": 1.25, "symmetry": 1.1},
        contest_bonus={"abomination": 22, "flower": 6, "people": 10},
        humour="Judges either waste or award first place. No middle ground.",
        discovery_hint="A bloom that looks mildly disappointed in your life choices.",
    ),
    "multi_stem": MutationDef(
        id="multi_stem",
        name="Multiple Stems",
        description="Several primary stems erupt from the crown.",
        rarity=0.04,
        mode=Dominance.INCOMPLETE,
        trait_mods={"branch": 1.4, "yield": 1.2, "stem": 0.85, "water": 0.9},
        contest_bonus={"giant": 6, "people": 3},
        humour="One plant. Several opinions about which way is up.",
        discovery_hint="A plant that can't agree on a single spine.",
    ),
    "rainbow_shift": MutationDef(
        id="rainbow_shift",
        name="Chromatic Drift",
        description="Pigment cycles through unexpected hues as the plant ages.",
        rarity=0.018,
        mode=Dominance.DOMINANT_MUTATION,
        trait_mods={"quality": 1.3, "flower": 1.1},
        contest_bonus={"flower": 10, "abomination": 8, "people": 7},
        humour="Colour charts weep in its presence.",
        discovery_hint="Petals that refuse to pick a favourite colour.",
    ),
    "glass_stem": MutationDef(
        id="glass_stem",
        name="Translucent Stem",
        description="Stem tissue turns semi-transparent, revealing sap flow.",
        rarity=0.025,
        mode=Dominance.RECESSIVE_MUTATION,
        trait_mods={"stem": 0.7, "quality": 1.35, "disease": 0.8},
        contest_bonus={"flower": 7, "abomination": 9},
        humour="Beautiful. Structurally concerning. Do not lean on it.",
        discovery_hint="A stem you can almost read through.",
    ),
    "thunder_bloom": MutationDef(
        id="thunder_bloom",
        name="Sonic Bloom",
        description="Flowers emit a soft pop when they open.",
        rarity=0.008,
        mode=Dominance.RECESSIVE_MUTATION,
        trait_mods={"flower": 1.2, "growth": 1.1, "stability": 0.8},
        contest_bonus={"abomination": 14, "speed": 5, "people": 9},
        humour="Neighbours complain. Judges lean in.",
        discovery_hint="A floral percussion section nobody asked for.",
    ),
}


WILDTYPE = "wt"
MUTANT = "mut"


def mutation_locus(mutation_id: str) -> Locus:
    mut = MUTATION_CATALOG[mutation_id]
    mode = mut.mode
    if mode == Dominance.RECESSIVE_MUTATION:
        # wt dominant over mut
        alleles = (
            Allele(WILDTYPE, "Wild-type", 0.0, dominance_rank=1),
            Allele(MUTANT, mut.name, 1.0, dominance_rank=0),
        )
        dom_mode = Dominance.COMPLETE
    elif mode == Dominance.DOMINANT_MUTATION:
        alleles = (
            Allele(WILDTYPE, "Wild-type", 0.0, dominance_rank=0),
            Allele(MUTANT, mut.name, 1.0, dominance_rank=1),
        )
        dom_mode = Dominance.COMPLETE
    else:
        alleles = (
            Allele(WILDTYPE, "Wild-type", 0.0, dominance_rank=0),
            Allele(MUTANT, mut.name, 1.0, dominance_rank=1),
        )
        dom_mode = Dominance.INCOMPLETE

    return Locus(
        name=f"mut_{mutation_id}",
        display_name=mut.name,
        mode=dom_mode,
        alleles=alleles,
        description=mut.description,
        hidden_until_expressed=True,
    )


MUTATION_LOCI: Dict[str, Locus] = {
    mid: mutation_locus(mid) for mid in MUTATION_CATALOG
}


def mutation_expressed(genotype_pair: Tuple[str, str], mutation_id: str) -> bool:
    """Whether a mutation shows in the phenotype."""
    mut = MUTATION_CATALOG[mutation_id]
    a, b = genotype_pair
    has = (a == MUTANT, b == MUTANT)
    if mut.mode == Dominance.RECESSIVE_MUTATION:
        return has == (True, True)
    if mut.mode == Dominance.DOMINANT_MUTATION:
        return has[0] or has[1]
    # Incomplete: heterozygous shows partial — count as expressed for discovery
    return has[0] or has[1]


def mutation_carrier(genotype_pair: Tuple[str, str], mutation_id: str) -> bool:
    """Carries mutant allele without full expression (hidden gene)."""
    a, b = genotype_pair
    if MUTANT not in (a, b):
        return False
    return not mutation_expressed(genotype_pair, mutation_id)


def mutation_strength(genotype_pair: Tuple[str, str], mutation_id: str) -> float:
    """0.0–1.0 expression strength for modifiers."""
    mut = MUTATION_CATALOG[mutation_id]
    a, b = genotype_pair
    count = int(a == MUTANT) + int(b == MUTANT)
    if mut.mode == Dominance.RECESSIVE_MUTATION:
        return 1.0 if count == 2 else 0.0
    if mut.mode == Dominance.DOMINANT_MUTATION:
        return 1.0 if count >= 1 else 0.0
    # Incomplete
    return {0: 0.0, 1: 0.55, 2: 1.0}[count]


def rarity_label(rarity: float) -> str:
    if rarity >= 0.035:
        return "Uncommon"
    if rarity >= 0.018:
        return "Rare"
    if rarity >= 0.01:
        return "Very Rare"
    return "Legendary"


def get_mutation(mutation_id: str) -> Optional[MutationDef]:
    return MUTATION_CATALOG.get(mutation_id)

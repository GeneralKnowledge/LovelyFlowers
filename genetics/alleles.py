"""Allele and locus definitions for the plant genome."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple


class Dominance(Enum):
    ADDITIVE = "additive"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    RECESSIVE_MUTATION = "recessive_mutation"
    DOMINANT_MUTATION = "dominant_mutation"


@dataclass(frozen=True)
class Allele:
    """A single allele variant at a locus."""

    id: str
    label: str
    value: float
    dominance_rank: int = 0  # higher wins under COMPLETE dominance


@dataclass(frozen=True)
class Locus:
    """A gene locus with possible alleles and inheritance mode."""

    name: str
    display_name: str
    mode: Dominance
    alleles: Tuple[Allele, ...]
    description: str = ""
    hidden_until_expressed: bool = False

    def allele_by_id(self, allele_id: str) -> Allele:
        for allele in self.alleles:
            if allele.id == allele_id:
                return allele
        raise KeyError(f"Unknown allele {allele_id!r} at locus {self.name}")

    def default_pair(self) -> Tuple[str, str]:
        mid = self.alleles[len(self.alleles) // 2]
        return (mid.id, mid.id)


def _quant(name: str, levels: List[Tuple[str, str, float]]) -> Locus:
    alleles = tuple(
        Allele(id=aid, label=label, value=value, dominance_rank=i)
        for i, (aid, label, value) in enumerate(levels)
    )
    return Locus(
        name=name,
        display_name=name.replace("_", " ").title(),
        mode=Dominance.ADDITIVE,
        alleles=alleles,
    )


# Quantitative trait loci (additive / partial dominance)
QUANTITATIVE_LOCI: Dict[str, Locus] = {
    "height": _quant(
        "height",
        [
            ("h0", "Dwarf", 0.15),
            ("h1", "Short", 0.35),
            ("h2", "Medium", 0.55),
            ("h3", "Tall", 0.75),
            ("h4", "Towering", 0.95),
        ],
    ),
    "width": _quant(
        "width",
        [
            ("w0", "Pencil", 0.15),
            ("w1", "Narrow", 0.35),
            ("w2", "Average", 0.55),
            ("w3", "Broad", 0.75),
            ("w4", "Sprawling", 0.95),
        ],
    ),
    "growth": _quant(
        "growth",
        [
            ("g0", "Glacial", 0.15),
            ("g1", "Slow", 0.35),
            ("g2", "Steady", 0.55),
            ("g3", "Brisk", 0.75),
            ("g4", "Explosive", 0.95),
        ],
    ),
    "yield": _quant(
        "yield",
        [
            ("y0", "Sparse", 0.15),
            ("y1", "Modest", 0.35),
            ("y2", "Fair", 0.55),
            ("y3", "Abundant", 0.75),
            ("y4", "Overflowing", 0.95),
        ],
    ),
    "flower": _quant(
        "flower",
        [
            ("f0", "Bare", 0.15),
            ("f1", "Few", 0.35),
            ("f2", "Decent", 0.55),
            ("f3", "Dense", 0.75),
            ("f4", "Carpet", 0.95),
        ],
    ),
    "leaf": _quant(
        "leaf",
        [
            ("l0", "Tiny", 0.15),
            ("l1", "Small", 0.35),
            ("l2", "Normal", 0.55),
            ("l3", "Large", 0.75),
            ("l4", "Enormous", 0.95),
        ],
    ),
    "branch": _quant(
        "branch",
        [
            ("b0", "Single", 0.15),
            ("b1", "Sparse", 0.35),
            ("b2", "Forked", 0.55),
            ("b3", "Bushy", 0.75),
            ("b4", "Thicket", 0.95),
        ],
    ),
    "stem": _quant(
        "stem",
        [
            ("s0", "Fragile", 0.15),
            ("s1", "Soft", 0.35),
            ("s2", "Firm", 0.55),
            ("s3", "Sturdy", 0.75),
            ("s4", "Ironwood", 0.95),
        ],
    ),
    "water": _quant(
        "water",
        [
            ("u0", "Thirsty", 0.15),
            ("u1", "Needy", 0.35),
            ("u2", "Average", 0.55),
            ("u3", "Efficient", 0.75),
            ("u4", "Camel", 0.95),
        ],
    ),
    "disease": _quant(
        "disease",
        [
            ("d0", "Fragile", 0.15),
            ("d1", "Susceptible", 0.35),
            ("d2", "Hardy", 0.55),
            ("d3", "Resistant", 0.75),
            ("d4", "Immune", 0.95),
        ],
    ),
    "quality": _quant(
        "quality",
        [
            ("q0", "Rough", 0.15),
            ("q1", "Common", 0.35),
            ("q2", "Fine", 0.55),
            ("q3", "Superb", 0.75),
            ("q4", "Museum", 0.95),
        ],
    ),
    "stability": _quant(
        "stability",
        [
            ("t0", "Chaotic", 0.15),
            ("t1", "Unstable", 0.35),
            ("t2", "Steady", 0.55),
            ("t3", "Stable", 0.75),
            ("t4", "Locked", 0.95),
        ],
    ),
}


# Mendelian colour / shape loci
COLOUR_LOCUS = Locus(
    name="colour",
    display_name="Pigment",
    mode=Dominance.COMPLETE,
    alleles=(
        Allele("c_green", "Green", 0.0, dominance_rank=1),
        Allele("c_yellow", "Yellow", 1.0, dominance_rank=2),
        Allele("c_orange", "Orange", 2.0, dominance_rank=3),
        Allele("c_red", "Red", 3.0, dominance_rank=4),
        Allele("c_pink", "Pink", 4.0, dominance_rank=5),
        Allele("c_purple", "Purple", 5.0, dominance_rank=6),
        Allele("c_blue", "Blue", 6.0, dominance_rank=7),
        Allele("c_white", "White", 7.0, dominance_rank=0),  # recessive
        Allele("c_black", "Midnight", 8.0, dominance_rank=8),
    ),
    description="Flower pigment. White is recessive; darker hues tend to dominate.",
)

SHAPE_LOCUS = Locus(
    name="shape",
    display_name="Bloom Shape",
    mode=Dominance.COMPLETE,
    alleles=(
        Allele("sh_round", "Round", 0.0, dominance_rank=1),
        Allele("sh_star", "Star", 1.0, dominance_rank=2),
        Allele("sh_trumpet", "Trumpet", 2.0, dominance_rank=3),
        Allele("sh_spike", "Spike", 3.0, dominance_rank=4),
        Allele("sh_bell", "Bell", 4.0, dominance_rank=2),
        Allele("sh_flat", "Saucer", 5.0, dominance_rank=1),
    ),
    description="Primary flower silhouette.",
)

SYMMETRY_LOCUS = Locus(
    name="symmetry",
    display_name="Symmetry",
    mode=Dominance.INCOMPLETE,
    alleles=(
        Allele("sy0", "Lopsided", 0.2, dominance_rank=0),
        Allele("sy1", "Uneven", 0.4, dominance_rank=1),
        Allele("sy2", "Balanced", 0.6, dominance_rank=2),
        Allele("sy3", "Mirror", 0.8, dominance_rank=3),
        Allele("sy4", "Perfect", 1.0, dominance_rank=4),
    ),
    description="Floral and structural symmetry. Incomplete dominance.",
    hidden_until_expressed=True,
)

MENDELIAN_LOCI: Dict[str, Locus] = {
    "colour": COLOUR_LOCUS,
    "shape": SHAPE_LOCUS,
    "symmetry": SYMMETRY_LOCUS,
}

ALL_BASE_LOCI: Dict[str, Locus] = {**QUANTITATIVE_LOCI, **MENDELIAN_LOCI}


def express_pair(locus: Locus, a_id: str, b_id: str) -> float:
    """Return a numeric expressed value for a diploid pair."""
    a = locus.allele_by_id(a_id)
    b = locus.allele_by_id(b_id)
    if locus.mode == Dominance.ADDITIVE:
        return (a.value + b.value) / 2.0
    if locus.mode == Dominance.INCOMPLETE:
        return (a.value + b.value) / 2.0
    if locus.mode == Dominance.COMPLETE:
        winner = a if a.dominance_rank >= b.dominance_rank else b
        return winner.value
    return (a.value + b.value) / 2.0


def express_allele_id(locus: Locus, a_id: str, b_id: str) -> str:
    """Return the phenotype allele id for complete/incomplete display."""
    a = locus.allele_by_id(a_id)
    b = locus.allele_by_id(b_id)
    if locus.mode == Dominance.COMPLETE:
        winner = a if a.dominance_rank >= b.dominance_rank else b
        return winner.id
    if a.id == b.id:
        return a.id
    # Incomplete / additive heterozygote — pick higher label for display tags
    return a.id if a.value >= b.value else b.id


def is_homozygous(a_id: str, b_id: str) -> bool:
    return a_id == b_id


def carries_recessive(locus: Locus, a_id: str, b_id: str, target_id: str) -> bool:
    """True if genotype carries target but does not fully express it under complete dominance."""
    if target_id not in (a_id, b_id):
        return False
    expressed = express_allele_id(locus, a_id, b_id)
    return expressed != target_id

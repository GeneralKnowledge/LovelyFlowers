"""Phenotype expression — genotype to visible/measurable traits with trade-offs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from genetics.alleles import (
    ALL_BASE_LOCI,
    COLOUR_LOCUS,
    SHAPE_LOCUS,
    express_allele_id,
    express_pair,
)
from genetics.mutations import (
    MUTATION_CATALOG,
    MUTATION_LOCI,
    mutation_carrier,
    mutation_expressed,
    mutation_strength,
)


COLOUR_RGB: Dict[str, Tuple[int, int, int]] = {
    "c_green": (86, 160, 72),
    "c_yellow": (230, 200, 55),
    "c_orange": (230, 130, 40),
    "c_red": (210, 55, 55),
    "c_pink": (230, 120, 160),
    "c_purple": (140, 70, 190),
    "c_blue": (70, 120, 220),
    "c_white": (240, 240, 235),
    "c_black": (40, 40, 50),
}


@dataclass
class Phenotype:
    """Fully expressed plant traits used by UI, value, and competitions."""

    # Core stats 0–1 (after trade-offs / mutations)
    height: float
    width: float
    growth: float
    yield_: float
    flower: float
    leaf: float
    branch: float
    stem: float
    water: float
    disease: float
    quality: float
    stability: float
    symmetry: float

    colour_id: str
    colour_rgb: Tuple[int, int, int]
    shape_id: str

    # Derived
    maturity_days: float
    beauty: float
    size_score: float
    speed_score: float
    strangeness: float
    value: float

    expressed_mutations: List[str] = field(default_factory=list)
    carrier_mutations: List[str] = field(default_factory=list)
    trait_notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict:
        return {
            "height": self.height,
            "width": self.width,
            "growth": self.growth,
            "yield": self.yield_,
            "flower": self.flower,
            "leaf": self.leaf,
            "branch": self.branch,
            "stem": self.stem,
            "water": self.water,
            "disease": self.disease,
            "quality": self.quality,
            "stability": self.stability,
            "symmetry": self.symmetry,
            "colour_id": self.colour_id,
            "colour_rgb": list(self.colour_rgb),
            "shape_id": self.shape_id,
            "maturity_days": self.maturity_days,
            "beauty": self.beauty,
            "size_score": self.size_score,
            "speed_score": self.speed_score,
            "strangeness": self.strangeness,
            "value": self.value,
            "expressed_mutations": list(self.expressed_mutations),
            "carrier_mutations": list(self.carrier_mutations),
            "trait_notes": list(self.trait_notes),
        }


def _clamp(v: float, lo: float = 0.05, hi: float = 1.35) -> float:
    return max(lo, min(hi, v))


def _apply_tradeoffs(traits: Dict[str, float], notes: List[str]) -> Dict[str, float]:
    """Natural trade-offs. Rare genetics can still overcome these via high stem/disease/etc."""
    t = dict(traits)

    # Fast maturity / growth normally lowers yield
    if t["growth"] > 0.7:
        penalty = (t["growth"] - 0.7) * 0.35
        t["yield"] = _clamp(t["yield"] - penalty, 0.05, 1.4)
        notes.append("Rapid growth taxes yield")

    # Large size stretches maturity (handled via maturity_days) and needs stem
    size = (t["height"] + t["width"]) / 2
    if size > 0.7 and t["stem"] < 0.55:
        t["quality"] = _clamp(t["quality"] - 0.12, 0.05, 1.4)
        notes.append("Size outpaces structural strength")

    # Dense flowers raise disease risk
    if t["flower"] > 0.7:
        t["disease"] = _clamp(t["disease"] - (t["flower"] - 0.7) * 0.4, 0.05, 1.4)
        notes.append("Dense blooms invite pathogens")

    # Explosive growth can weaken stems
    if t["growth"] > 0.75:
        t["stem"] = _clamp(t["stem"] - (t["growth"] - 0.75) * 0.35, 0.05, 1.4)
        notes.append("Hasty growth softens stems")

    # Huge yield needs supporting genetics
    if t["yield"] > 0.75 and t["stem"] < 0.5:
        t["yield"] = _clamp(t["yield"] * 0.85, 0.05, 1.4)
        notes.append("Yield collapses without support")

    # Water stress hurts quality if inefficient
    if t["water"] < 0.35:
        t["quality"] = _clamp(t["quality"] - 0.08, 0.05, 1.4)

    return t


def express_phenotype(genotype: Dict[str, Tuple[str, str]]) -> Phenotype:
    """Convert a full genotype into a phenotype with trade-offs and mutations."""
    notes: List[str] = []
    traits: Dict[str, float] = {}

    for name, locus in ALL_BASE_LOCI.items():
        if name in ("colour", "shape"):
            continue
        a, b = genotype[name]
        traits[name] = express_pair(locus, a, b)

    colour_id = express_allele_id(COLOUR_LOCUS, *genotype["colour"])
    shape_id = express_allele_id(SHAPE_LOCUS, *genotype["shape"])
    colour_rgb = COLOUR_RGB.get(colour_id, (120, 160, 90))

    expressed: List[str] = []
    carriers: List[str] = []

    for mid, locus in MUTATION_LOCI.items():
        key = locus.name
        if key not in genotype:
            continue
        pair = genotype[key]
        strength = mutation_strength(pair, mid)
        if mutation_expressed(pair, mid):
            expressed.append(mid)
            mut = MUTATION_CATALOG[mid]
            for trait, mult in mut.trait_mods.items():
                if trait == "symmetry":
                    traits["symmetry"] = _clamp(
                        traits.get("symmetry", 0.5) * (1 + (mult - 1) * strength)
                    )
                elif trait in traits:
                    # mult > 1 boosts; < 1 penalises, scaled by strength
                    base = traits[trait]
                    traits[trait] = _clamp(base * (1 + (mult - 1) * strength))
            notes.append(f"Mutation expressed: {mut.name}")
        elif mutation_carrier(pair, mid):
            carriers.append(mid)

    # Rainbow mutation shifts colour presentation
    if "rainbow_shift" in expressed:
        colour_rgb = (
            min(255, colour_rgb[0] + 40),
            min(255, (colour_rgb[1] + 80) % 200 + 55),
            min(255, colour_rgb[2] + 60),
        )

    if "bioluminescence" in expressed:
        colour_rgb = (
            min(255, int(colour_rgb[0] * 0.7 + 80)),
            min(255, int(colour_rgb[1] * 0.7 + 120)),
            min(255, int(colour_rgb[2] * 0.7 + 140)),
        )

    traits = _apply_tradeoffs(traits, notes)

    # Maturity: base 8 days, modified by growth (fast = fewer days) and size (big = more)
    size = (traits["height"] + traits["width"]) / 2
    maturity_days = 10.0 * (1.35 - traits["growth"] * 0.7) * (0.85 + size * 0.4)
    maturity_days = max(3.0, min(22.0, maturity_days))

    beauty = (
        traits["flower"] * 0.35
        + traits["quality"] * 0.25
        + traits["symmetry"] * 0.25
        + traits.get("leaf", 0.5) * 0.05
        + (0.1 if colour_id not in ("c_green",) else 0.0)
    )
    beauty = _clamp(beauty, 0.05, 1.5)

    size_score = _clamp(
        traits["height"] * 0.4
        + traits["width"] * 0.2
        + traits["yield"] * 0.25
        + traits["stem"] * 0.15,
        0.05,
        1.5,
    )
    speed_score = _clamp(
        traits["growth"] * 0.7 + (1.0 - (maturity_days - 3) / 19.0) * 0.3,
        0.05,
        1.5,
    )
    strangeness = (
        0.15 * len(expressed)
        + 0.05 * len(carriers)
        + 0.2 * sum(1 for m in expressed if MUTATION_CATALOG[m].rarity < 0.02)
    )
    if expressed:
        strangeness = max(strangeness, 0.35 + 0.12 * len(expressed))
    strangeness = _clamp(strangeness, 0.0, 1.5)

    # Market value — simple disposal price
    mutation_value = sum(
        (0.08 / max(MUTATION_CATALOG[m].rarity, 0.005)) * 0.5 for m in expressed
    )
    value = (
        8
        + beauty * 28
        + size_score * 22
        + speed_score * 12
        + traits["yield"] * 18
        + traits["quality"] * 16
        + strangeness * 20
        + mutation_value
    )
    value = round(max(3.0, value), 1)

    return Phenotype(
        height=round(traits["height"], 3),
        width=round(traits["width"], 3),
        growth=round(traits["growth"], 3),
        yield_=round(traits["yield"], 3),
        flower=round(traits["flower"], 3),
        leaf=round(traits["leaf"], 3),
        branch=round(traits["branch"], 3),
        stem=round(traits["stem"], 3),
        water=round(traits["water"], 3),
        disease=round(traits["disease"], 3),
        quality=round(traits["quality"], 3),
        stability=round(traits["stability"], 3),
        symmetry=round(traits["symmetry"], 3),
        colour_id=colour_id,
        colour_rgb=colour_rgb,
        shape_id=shape_id,
        maturity_days=round(maturity_days, 2),
        beauty=round(beauty, 3),
        size_score=round(size_score, 3),
        speed_score=round(speed_score, 3),
        strangeness=round(strangeness, 3),
        value=value,
        expressed_mutations=expressed,
        carrier_mutations=carriers,
        trait_notes=notes,
    )

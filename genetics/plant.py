"""Plant individuals, seed generation, and breeding."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from genetics.alleles import ALL_BASE_LOCI, Allele
from genetics.mutations import (
    MUTANT,
    MUTATION_CATALOG,
    MUTATION_LOCI,
    WILDTYPE,
    mutation_expressed,
)
from genetics.phenotype import Phenotype, express_phenotype


Genotype = Dict[str, Tuple[str, str]]


@dataclass
class Plant:
    """A single owned specimen (plant, fungus, hybrid, or worse)."""

    id: str
    name: str
    genotype: Genotype
    generation: int
    parent_ids: Tuple[Optional[str], Optional[str]]
    age_days: float = 0.0
    planted: bool = False
    mature: bool = False
    growth_progress: float = 0.0  # 0–1 while growing
    competition_history: List[Dict] = field(default_factory=list)
    trial_history: List[Dict] = field(default_factory=list)
    notes: str = ""
    favourite: bool = False
    sold: bool = False
    species_kind: str = "plant"  # plant, fungus, lichen, mossbeast, bloomcritter, hybrid
    origin: str = "home"  # location id
    wild: bool = False
    irradiated: bool = False

    # Cached phenotype (recomputed when needed)
    _phenotype: Optional[Phenotype] = field(default=None, repr=False)

    def phenotype(self, refresh: bool = False) -> Phenotype:
        if self._phenotype is None or refresh:
            self._phenotype = express_phenotype(self.genotype)
        return self._phenotype

    @property
    def value(self) -> float:
        return self.phenotype().value

    def expressed_mutation_names(self) -> List[str]:
        ph = self.phenotype()
        return [MUTATION_CATALOG[m].name for m in ph.expressed_mutations]

    def pedigree_summary(self) -> Dict:
        ph = self.phenotype()
        return {
            "id": self.id,
            "name": self.name,
            "generation": self.generation,
            "parent_ids": list(self.parent_ids),
            "mutations": list(ph.expressed_mutations),
            "carrier_mutations": list(ph.carrier_mutations),
            "colour": ph.colour_id,
            "shape": ph.shape_id,
            "wins": [
                c for c in self.competition_history if c.get("place", 99) <= 3
            ],
        }

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "genotype": {k: list(v) for k, v in self.genotype.items()},
            "generation": self.generation,
            "parent_ids": list(self.parent_ids),
            "age_days": self.age_days,
            "planted": self.planted,
            "mature": self.mature,
            "growth_progress": self.growth_progress,
            "competition_history": list(self.competition_history),
            "trial_history": list(self.trial_history),
            "notes": self.notes,
            "favourite": self.favourite,
            "sold": self.sold,
            "species_kind": self.species_kind,
            "origin": self.origin,
            "wild": self.wild,
            "irradiated": self.irradiated,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Plant":
        genotype = {k: (v[0], v[1]) for k, v in data["genotype"].items()}
        parents = data.get("parent_ids", [None, None])
        return cls(
            id=data["id"],
            name=data["name"],
            genotype=genotype,
            generation=data.get("generation", 1),
            parent_ids=(parents[0], parents[1]),
            age_days=data.get("age_days", 0.0),
            planted=data.get("planted", False),
            mature=data.get("mature", False),
            growth_progress=data.get("growth_progress", 0.0),
            competition_history=list(data.get("competition_history", [])),
            trial_history=list(data.get("trial_history", [])),
            notes=data.get("notes", ""),
            favourite=data.get("favourite", False),
            sold=data.get("sold", False),
            species_kind=data.get("species_kind", "plant"),
            origin=data.get("origin", "home"),
            wild=data.get("wild", False),
            irradiated=data.get("irradiated", False),
        )


def _pick_weighted_allele(alleles: Tuple[Allele, ...], rng: random.Random, bias_mid: bool = True) -> str:
    if not bias_mid:
        return rng.choice(alleles).id
    # Bell-ish weights toward middle alleles for starter seeds
    weights = []
    mid = (len(alleles) - 1) / 2
    for i, _ in enumerate(alleles):
        dist = abs(i - mid)
        weights.append(max(0.5, 3.0 - dist))
    return rng.choices(alleles, weights=weights, k=1)[0].id


def random_base_genotype(rng: random.Random, quality: str = "common") -> Genotype:
    """Create a random diploid genotype for a new seed line."""
    genotype: Genotype = {}
    for name, locus in ALL_BASE_LOCI.items():
        if quality == "common":
            a = _pick_weighted_allele(locus.alleles, rng, bias_mid=True)
            b = _pick_weighted_allele(locus.alleles, rng, bias_mid=True)
        elif quality == "premium":
            # Slightly better allele bias
            alleles = locus.alleles
            weights = [0.5 + a.value for a in alleles]
            a = rng.choices(alleles, weights=weights, k=1)[0].id
            b = rng.choices(alleles, weights=weights, k=1)[0].id
        else:  # exotic — wider variance
            a = rng.choice(locus.alleles).id
            b = rng.choice(locus.alleles).id
        genotype[name] = (a, b)

    for mid, locus in MUTATION_LOCI.items():
        # Starters almost never carry mutations; exotic seeds rarely do
        carry_chance = {"common": 0.01, "premium": 0.03, "exotic": 0.08}[quality]
        if rng.random() < carry_chance:
            genotype[locus.name] = (WILDTYPE, MUTANT)
        else:
            genotype[locus.name] = (WILDTYPE, WILDTYPE)
    return genotype


def create_seed_plant(
    name: str,
    rng: Optional[random.Random] = None,
    quality: str = "common",
    generation: int = 1,
) -> Plant:
    rng = rng or random.Random()
    plant = Plant(
        id=str(uuid.uuid4())[:8],
        name=name,
        genotype=random_base_genotype(rng, quality=quality),
        generation=generation,
        parent_ids=(None, None),
    )
    plant.phenotype()  # cache
    return plant


def _gamete(genotype: Genotype, rng: random.Random) -> Dict[str, str]:
    """Mendelian segregation — one random allele per locus."""
    haploid: Dict[str, str] = {}
    for locus, pair in genotype.items():
        haploid[locus] = rng.choice(pair)
    return haploid


def _maybe_mutate(
    genotype: Genotype,
    stability: float,
    rng: random.Random,
) -> List[str]:
    """Spontaneous mutation events. Lower stability → more chaos."""
    new_mutations: List[str] = []
    # Base spontaneous rate scaled by instability
    chaos = max(0.15, 1.2 - stability)
    for mid, mut in MUTATION_CATALOG.items():
        key = f"mut_{mid}"
        pair = genotype.get(key, (WILDTYPE, WILDTYPE))
        # Chance to gain a mutant allele if not already homozygous mutant
        rate = mut.rarity * chaos
        if pair.count(MUTANT) < 2 and rng.random() < rate:
            # Replace a wildtype allele with mutant
            alleles = list(pair)
            for i, al in enumerate(alleles):
                if al == WILDTYPE:
                    alleles[i] = MUTANT
                    break
            genotype[key] = (alleles[0], alleles[1])
            new_mutations.append(mid)
        # Rare chance for back-mutation / loss if unstable
        elif pair.count(MUTANT) > 0 and stability < 0.4 and rng.random() < 0.02 * chaos:
            alleles = list(pair)
            for i, al in enumerate(alleles):
                if al == MUTANT:
                    alleles[i] = WILDTYPE
                    break
            genotype[key] = (alleles[0], alleles[1])
    return new_mutations


def breed(
    parent_a: Plant,
    parent_b: Plant,
    name: str,
    rng: Optional[random.Random] = None,
) -> Plant:
    """Breed two plants — true allele inheritance + possible mutation."""
    rng = rng or random.Random()
    ga = _gamete(parent_a.genotype, rng)
    gb = _gamete(parent_b.genotype, rng)

    child_genotype: Genotype = {}
    all_loci = set(ga) | set(gb) | set(ALL_BASE_LOCI) | {loc.name for loc in MUTATION_LOCI.values()}
    for locus in all_loci:
        a = ga.get(locus, WILDTYPE if locus.startswith("mut_") else ALL_BASE_LOCI.get(locus, None) and ALL_BASE_LOCI[locus].default_pair()[0])
        b = gb.get(locus, WILDTYPE if locus.startswith("mut_") else None)
        if a is None or b is None:
            if locus in ALL_BASE_LOCI:
                a = a or ALL_BASE_LOCI[locus].default_pair()[0]
                b = b or ALL_BASE_LOCI[locus].default_pair()[1]
            else:
                a = a or WILDTYPE
                b = b or WILDTYPE
        # Randomise order so display isn't parent-biased
        pair = [a, b]
        rng.shuffle(pair)
        child_genotype[locus] = (pair[0], pair[1])

    # Estimate stability from parents for mutation pressure
    stab_a = parent_a.phenotype().stability
    stab_b = parent_b.phenotype().stability
    stability_est = (stab_a + stab_b) / 2
    _maybe_mutate(child_genotype, stability_est, rng)

    generation = max(parent_a.generation, parent_b.generation) + 1
    from genetics.kinds import hybrid_kind

    kind = hybrid_kind(
        getattr(parent_a, "species_kind", "plant"),
        getattr(parent_b, "species_kind", "plant"),
    )
    # Hybrids are less stable — nudge stability down sometimes
    if kind == "hybrid" and "stability" in child_genotype and rng.random() < 0.55:
        a, b = child_genotype["stability"]
        order = ["t0", "t1", "t2", "t3", "t4"]

        def down(x: str) -> str:
            if x not in order:
                return "t1"
            return order[max(0, order.index(x) - 1)]

        child_genotype["stability"] = (down(a), down(b))

    child = Plant(
        id=str(uuid.uuid4())[:8],
        name=name,
        genotype=child_genotype,
        generation=generation,
        parent_ids=(parent_a.id, parent_b.id),
        species_kind=kind,
        origin=getattr(parent_a, "origin", "home"),
        notes="Hybrid abomination." if kind == "hybrid" else "",
    )
    child.phenotype()
    return child


def breed_litter(
    parent_a: Plant,
    parent_b: Plant,
    name_fn,
    count: int = 3,
    rng: Optional[random.Random] = None,
) -> List[Plant]:
    """Produce multiple offspring from a cross."""
    rng = rng or random.Random()
    return [breed(parent_a, parent_b, name_fn(i), rng=rng) for i in range(count)]


def describe_hidden_genetics(plant: Plant, discovered_mutations: set) -> List[str]:
    """Player-facing genetics notes; unknown mutations show as ???"""
    ph = plant.phenotype()
    lines = []
    for mid in ph.expressed_mutations:
        mut = MUTATION_CATALOG[mid]
        if mid in discovered_mutations:
            lines.append(f"Expressed: {mut.name}")
        else:
            lines.append("Expressed: ???")
    for mid in ph.carrier_mutations:
        if mid in discovered_mutations:
            lines.append(f"Carrier (hidden): {MUTATION_CATALOG[mid].name}")
        else:
            lines.append("Carrier (hidden): ???")
    return lines


def genotype_carries_expressed(plant: Plant, mutation_id: str) -> bool:
    key = f"mut_{mutation_id}"
    if key not in plant.genotype:
        return False
    return mutation_expressed(plant.genotype[key], mutation_id)

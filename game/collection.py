"""Discovery / collection log for traits, mutations, colours, winners, bloodlines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from genetics.alleles import COLOUR_LOCUS, SHAPE_LOCUS
from genetics.mutations import MUTATION_CATALOG, rarity_label
from genetics.plant import Plant


COLOUR_LABELS = {a.id: a.label for a in COLOUR_LOCUS.alleles}
SHAPE_LABELS = {a.id: a.label for a in SHAPE_LOCUS.alleles}


@dataclass
class CollectionLog:
    mutations: Set[str] = field(default_factory=set)
    colours: Set[str] = field(default_factory=set)
    shapes: Set[str] = field(default_factory=set)
    winners: List[Dict] = field(default_factory=list)
    bloodlines: Set[str] = field(default_factory=set)
    max_generation: int = 1
    plants_owned_total: int = 0

    def discover_from_plant(self, plant: Plant) -> List[str]:
        """Update collection from a plant; return newly discovered labels."""
        ph = plant.phenotype()
        found: List[str] = []

        if ph.colour_id not in self.colours:
            self.colours.add(ph.colour_id)
            found.append(f"Colour: {COLOUR_LABELS.get(ph.colour_id, ph.colour_id)}")

        if ph.shape_id not in self.shapes:
            self.shapes.add(ph.shape_id)
            found.append(f"Shape: {SHAPE_LABELS.get(ph.shape_id, ph.shape_id)}")

        for mid in ph.expressed_mutations:
            if mid not in self.mutations:
                self.mutations.add(mid)
                mut = MUTATION_CATALOG[mid]
                found.append(f"Mutation: {mut.name} ({rarity_label(mut.rarity)})")

        # Bloodline root name
        root = plant.name.split()[0]
        if root.startswith("The"):
            root = plant.name
        if plant.generation >= 3 and root not in self.bloodlines:
            self.bloodlines.add(root)
            found.append(f"Bloodline: {root}")

        self.max_generation = max(self.max_generation, plant.generation)
        return found

    def record_win(self, result: Dict) -> None:
        if result.get("place", 99) <= 3:
            self.winners.append(result)

    def mutation_display(self, mutation_id: str) -> str:
        if mutation_id in self.mutations:
            return MUTATION_CATALOG[mutation_id].name
        return "???"

    def catalog_entries(self) -> List[Dict]:
        entries = []
        for mid, mut in MUTATION_CATALOG.items():
            known = mid in self.mutations
            entries.append(
                {
                    "id": mid,
                    "name": mut.name if known else "???",
                    "rarity": rarity_label(mut.rarity),
                    "known": known,
                    "description": mut.description if known else "Undiscovered mutation.",
                    "humour": mut.humour if known else "",
                }
            )
        return entries

    def to_dict(self) -> Dict:
        return {
            "mutations": sorted(self.mutations),
            "colours": sorted(self.colours),
            "shapes": sorted(self.shapes),
            "winners": list(self.winners),
            "bloodlines": sorted(self.bloodlines),
            "max_generation": self.max_generation,
            "plants_owned_total": self.plants_owned_total,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CollectionLog":
        return cls(
            mutations=set(data.get("mutations", [])),
            colours=set(data.get("colours", [])),
            shapes=set(data.get("shapes", [])),
            winners=list(data.get("winners", [])),
            bloodlines=set(data.get("bloodlines", [])),
            max_generation=data.get("max_generation", 1),
            plants_owned_total=data.get("plants_owned_total", 0),
        )

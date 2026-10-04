"""World locations — travel is simulated now; real movement comes later."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from genetics.kinds import KIND_LABELS

KIND_HUMOUR: Dict[str, str] = {
    "plant": "A plant. Relatively speaking.",
    "fungus": "Not a plant. Will argue otherwise in court.",
    "lichen": "A committee of organisms pretending to be one.",
    "mossbeast": "Moss that has learned to have opinions.",
    "bloomcritter": "Floral. Also faintly ambulatory. Don't ask.",
    "hybrid": "Taxonomy has left the building.",
}


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    tagline: str
    travel_cost: int
    travel_hours: float
    prestige_required: int
    wild_kinds: Tuple[str, ...]
    wild_quality: str
    mutation_bias: float
    special: Optional[str] = None
    flavour: str = ""


LOCATIONS: List[Location] = [
    Location(
        id="home",
        name="Home Greenhouse",
        tagline="Your breeding bench. Safe. Relatively.",
        travel_cost=0,
        travel_hours=0,
        prestige_required=0,
        wild_kinds=("plant",),
        wild_quality="common",
        mutation_bias=0.0,
        flavour="You are already here. The kettle is on.",
    ),
    Location(
        id="meadow",
        name="Weedy Meadow",
        tagline="Ordinary wildflowers with the occasional surprise.",
        travel_cost=8,
        travel_hours=4,
        prestige_required=0,
        wild_kinds=("plant", "plant", "lichen"),
        wild_quality="common",
        mutation_bias=0.08,
        flavour="Bees judge your shoes.",
    ),
    Location(
        id="fungal_hollow",
        name="Fungal Hollow",
        tagline="Things that are not plants, but will breed with them anyway.",
        travel_cost=18,
        travel_hours=6,
        prestige_required=3,
        wild_kinds=("fungus", "lichen", "mossbeast"),
        wild_quality="premium",
        mutation_bias=0.18,
        flavour="The air smells like damp secrets.",
    ),
    Location(
        id="radiation_flats",
        name="Radiation Flats",
        tagline="Glowing scrubland. Mutations optional. Mutations frequent.",
        travel_cost=28,
        travel_hours=8,
        prestige_required=6,
        wild_kinds=("plant", "bloomcritter", "fungus"),
        wild_quality="volatile",
        mutation_bias=0.45,
        special="radiation_zone",
        flavour="Your Geiger counter has opinions.",
    ),
    Location(
        id="scrap_bog",
        name="Scrapyard Bog",
        tagline="Half-machine moss and regrettable hybrids.",
        travel_cost=35,
        travel_hours=10,
        prestige_required=10,
        wild_kinds=("mossbeast", "bloomcritter", "plant"),
        wild_quality="exotic",
        mutation_bias=0.25,
        flavour="Something metal is photosynthesising.",
    ),
    Location(
        id="abandoned_lab",
        name="Abandoned Pollination Lab",
        tagline="Unlock radiation chamber tech. Also: bad ideas.",
        travel_cost=40,
        travel_hours=12,
        prestige_required=8,
        wild_kinds=("plant", "fungus"),
        wild_quality="exotic",
        mutation_bias=0.3,
        special="lab",
        flavour="Sticky notes say DO NOT CROSS-BREED. Tempting.",
    ),
]


def get_location(loc_id: str) -> Location:
    for loc in LOCATIONS:
        if loc.id == loc_id:
            return loc
    raise KeyError(loc_id)


def locations_for_prestige(prestige: int) -> List[Location]:
    return [loc for loc in LOCATIONS if loc.prestige_required <= prestige]

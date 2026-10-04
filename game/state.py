"""Greenhouse game state — buy, plant, grow, breed, sell, compete, save."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from game.collection import CollectionLog
from game.competitions import COMPETITIONS, ContestResult, get_competition, run_competition
from game.names import humorous_description, offspring_names, random_name
from genetics.plant import Plant, breed_litter, create_seed_plant


SEED_CATALOG = [
    {"id": "common", "name": "Common Seed Packet", "cost": 12, "quality": "common"},
    {"id": "premium", "name": "Premium Seed Packet", "cost": 35, "quality": "premium"},
    {"id": "exotic", "name": "Exotic Seed Packet", "cost": 80, "quality": "exotic"},
]

UPGRADES = [
    {
        "id": "bench",
        "name": "Extra Pot Bench",
        "cost": 60,
        "desc": "+2 greenhouse slots",
        "effect": "slots",
        "value": 2,
    },
    {
        "id": "wing",
        "name": "Greenhouse Wing",
        "cost": 150,
        "desc": "+3 greenhouse slots",
        "effect": "slots",
        "value": 3,
    },
    {
        "id": "lamps",
        "name": "Grow Lamps",
        "cost": 100,
        "desc": "Plants grow 25% faster",
        "effect": "grow_speed",
        "value": 0.25,
    },
    {
        "id": "lab",
        "name": "Pollination Lab",
        "cost": 120,
        "desc": "Breeding produces +1 offspring",
        "effect": "litter",
        "value": 1,
    },
]


@dataclass
class GameState:
    money: float = 100.0
    prestige: int = 0
    day: float = 1.0
    greenhouse_slots: int = 6
    grow_speed_bonus: float = 0.0
    litter_bonus: int = 0
    plants: Dict[str, Plant] = field(default_factory=dict)
    pot_assignments: List[Optional[str]] = field(default_factory=list)  # plant ids in pots
    owned_upgrades: List[str] = field(default_factory=list)
    collection: CollectionLog = field(default_factory=CollectionLog)
    messages: List[str] = field(default_factory=list)
    last_contest: Optional[Dict] = None
    rng_seed: int = 42
    _rng: random.Random = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self._rng is None:
            self._rng = random.Random(self.rng_seed)
        if not self.pot_assignments:
            self.pot_assignments = [None] * self.greenhouse_slots

    # --- messaging -----------------------------------------------------
    def log(self, text: str) -> None:
        self.messages.append(text)
        if len(self.messages) > 80:
            self.messages = self.messages[-80:]

    # --- queries -------------------------------------------------------
    def living_plants(self) -> List[Plant]:
        return [p for p in self.plants.values() if not p.sold]

    def mature_unpotted(self) -> List[Plant]:
        potted = set(x for x in self.pot_assignments if x)
        return [
            p
            for p in self.living_plants()
            if p.mature and p.id not in potted
        ]

    def plant_by_id(self, plant_id: str) -> Plant:
        return self.plants[plant_id]

    def used_names(self) -> set:
        return {p.name for p in self.plants.values()}

    # --- economy -------------------------------------------------------
    def buy_seed(self, quality: str = "common") -> Optional[Plant]:
        item = next((s for s in SEED_CATALOG if s["id"] == quality), None)
        if not item:
            self.log("Unknown seed type.")
            return None
        if self.money < item["cost"]:
            self.log(f"Not enough money for {item['name']} (${item['cost']}).")
            return None
        # Need a free pot to plant immediately? Seeds go to inventory as unplanted immature.
        # Design: buying a seed creates a plant that must be planted in a free pot.
        free = self._free_pot_index()
        if free is None:
            self.log("No free pots. Sell something or expand the greenhouse.")
            return None

        self.money -= item["cost"]
        name = random_name(self._rng, self.used_names())
        plant = create_seed_plant(name, rng=self._rng, quality=item["quality"])
        plant.planted = True
        plant.growth_progress = 0.0
        plant.mature = False
        self.plants[plant.id] = plant
        self.pot_assignments[free] = plant.id
        self.collection.plants_owned_total += 1
        discoveries = self.collection.discover_from_plant(plant)
        self.log(f"Planted {plant.name} from {item['name']}.")
        for d in discoveries:
            self.log(f"Discovered {d}!")
        return plant

    def sell_plant(self, plant_id: str) -> Optional[float]:
        plant = self.plants.get(plant_id)
        if not plant or plant.sold:
            self.log("Plant not found.")
            return None
        if plant.favourite:
            self.log(f"{plant.name} is marked favourite — unfavourite before selling.")
            return None
        value = plant.value
        # Immature plants sell for less
        if not plant.mature:
            value = round(value * 0.35, 1)
        plant.sold = True
        self._remove_from_pots(plant_id)
        self.money += value
        self.log(f"Sold {plant.name} for ${value:.1f}.")
        return value

    def buy_upgrade(self, upgrade_id: str) -> bool:
        up = next((u for u in UPGRADES if u["id"] == upgrade_id), None)
        if not up:
            self.log("Unknown upgrade.")
            return False
        if upgrade_id in self.owned_upgrades:
            self.log("Already owned.")
            return False
        if self.money < up["cost"]:
            self.log(f"Need ${up['cost']} for {up['name']}.")
            return False
        self.money -= up["cost"]
        self.owned_upgrades.append(upgrade_id)
        if up["effect"] == "slots":
            self.greenhouse_slots += up["value"]
            self.pot_assignments.extend([None] * up["value"])
        elif up["effect"] == "grow_speed":
            self.grow_speed_bonus += up["value"]
        elif up["effect"] == "litter":
            self.litter_bonus += up["value"]
        self.log(f"Purchased {up['name']}.")
        return True

    # --- growth --------------------------------------------------------
    def advance_time(self, hours: float = 6.0) -> List[str]:
        """Advance greenhouse time; return names of newly matured plants."""
        days = hours / 24.0
        self.day += days
        matured = []
        speed = 1.0 + self.grow_speed_bonus
        for pid in list(self.pot_assignments):
            if not pid:
                continue
            plant = self.plants[pid]
            if plant.mature or plant.sold:
                continue
            ph = plant.phenotype()
            plant.age_days += days
            rate = (days / ph.maturity_days) * speed
            plant.growth_progress = min(1.0, plant.growth_progress + rate)
            if plant.growth_progress >= 1.0:
                plant.mature = True
                plant.growth_progress = 1.0
                matured.append(plant.name)
                discoveries = self.collection.discover_from_plant(plant)
                self.log(f"{plant.name} has matured! {humorous_description(plant)}")
                for d in discoveries:
                    self.log(f"Discovered {d}!")
        return matured

    # --- breeding ------------------------------------------------------
    def can_breed(self, a_id: str, b_id: str) -> Tuple[bool, str]:
        if a_id == b_id:
            return False, "A plant cannot pollinate itself in this greenhouse."
        a = self.plants.get(a_id)
        b = self.plants.get(b_id)
        if not a or not b or a.sold or b.sold:
            return False, "Both parents must be living plants."
        if not a.mature or not b.mature:
            return False, "Both parents must be mature."
        free = self._count_free_pots()
        litter = 3 + self.litter_bonus
        if free < 1:
            return False, "Need at least one free pot for offspring."
        if free < litter:
            return True, f"Only {free} free pot(s); litter will be reduced."
        return True, f"Ready to breed ({min(litter, free)} offspring)."

    def breed_plants(self, a_id: str, b_id: str) -> List[Plant]:
        ok, msg = self.can_breed(a_id, b_id)
        if not ok:
            self.log(msg)
            return []
        a = self.plants[a_id]
        b = self.plants[b_id]
        litter = 3 + self.litter_bonus
        free = self._count_free_pots()
        count = min(litter, free)
        if count < 1:
            self.log("No room for offspring.")
            return []

        names = offspring_names(a, b, count, self._rng, self.used_names())
        children = breed_litter(
            a, b, name_fn=lambda i: names[i], count=count, rng=self._rng
        )
        for child in children:
            pot = self._free_pot_index()
            if pot is None:
                break
            child.planted = True
            child.mature = False
            child.growth_progress = 0.0
            self.plants[child.id] = child
            self.pot_assignments[pot] = child.id
            self.collection.plants_owned_total += 1
            # Discoveries for carriers happen on maturity mostly; still note colour genes
            self.collection.discover_from_plant(child)
            self.log(
                f"New seedling: {child.name} (Gen {child.generation}) "
                f"from {a.name} × {b.name}."
            )
        return children

    # --- competitions --------------------------------------------------
    def available_competitions(self) -> List:
        return [c for c in COMPETITIONS if self.prestige >= c.prestige_required]

    def enter_competition(self, comp_id: str, plant_id: str) -> Optional[ContestResult]:
        try:
            comp = get_competition(comp_id)
        except KeyError:
            self.log("Unknown competition.")
            return None
        if self.prestige < comp.prestige_required:
            self.log(f"Need {comp.prestige_required} prestige for {comp.name}.")
            return None
        plant = self.plants.get(plant_id)
        if not plant or plant.sold or not plant.mature:
            self.log("Select a mature plant to enter.")
            return None
        if self.money < comp.entry_fee:
            self.log(f"Entry fee is ${comp.entry_fee}.")
            return None

        self.money -= comp.entry_fee
        result = run_competition(comp, plant, self.prestige, rng=self._rng)
        self.money += result.prize
        self.prestige += result.prestige
        record = result.to_dict()
        plant.competition_history.append(record)
        self.collection.record_win(record)
        self.last_contest = record
        self.log(result.summary)
        if result.prize:
            self.log(f"Prize: ${result.prize}. Prestige +{result.prestige}.")
        return result

    # --- pedigree ------------------------------------------------------
    def pedigree_tree(self, plant_id: str, depth: int = 3) -> Dict:
        plant = self.plants.get(plant_id)
        if not plant:
            return {}
        return self._pedigree_node(plant, depth)

    def _pedigree_node(self, plant: Plant, depth: int) -> Dict:
        ph = plant.phenotype()
        node = {
            "id": plant.id,
            "name": plant.name,
            "generation": plant.generation,
            "colour": ph.colour_id,
            "mutations": [
                self.collection.mutation_display(m) for m in ph.expressed_mutations
            ],
            "carriers": [
                self.collection.mutation_display(m) for m in ph.carrier_mutations
            ],
            "wins": sum(1 for c in plant.competition_history if c.get("place", 99) <= 3),
            "parents": [],
        }
        if depth <= 0:
            return node
        for pid in plant.parent_ids:
            if pid and pid in self.plants:
                node["parents"].append(self._pedigree_node(self.plants[pid], depth - 1))
            elif pid:
                node["parents"].append({"id": pid, "name": "?", "generation": "?", "missing": True})
        return node

    def toggle_favourite(self, plant_id: str) -> None:
        plant = self.plants.get(plant_id)
        if plant and not plant.sold:
            plant.favourite = not plant.favourite
            state = "favourite" if plant.favourite else "unfavourited"
            self.log(f"{plant.name} marked {state}.")

    # --- pots helpers --------------------------------------------------
    def _free_pot_index(self) -> Optional[int]:
        for i, pid in enumerate(self.pot_assignments):
            if pid is None:
                return i
            p = self.plants.get(pid)
            if p is None or p.sold:
                self.pot_assignments[i] = None
                return i
        return None

    def _count_free_pots(self) -> int:
        n = 0
        for i, pid in enumerate(self.pot_assignments):
            if pid is None:
                n += 1
            else:
                p = self.plants.get(pid)
                if p is None or p.sold:
                    self.pot_assignments[i] = None
                    n += 1
        return n

    def _remove_from_pots(self, plant_id: str) -> None:
        for i, pid in enumerate(self.pot_assignments):
            if pid == plant_id:
                self.pot_assignments[i] = None

    # --- persistence ---------------------------------------------------
    def to_dict(self) -> Dict:
        return {
            "money": self.money,
            "prestige": self.prestige,
            "day": self.day,
            "greenhouse_slots": self.greenhouse_slots,
            "grow_speed_bonus": self.grow_speed_bonus,
            "litter_bonus": self.litter_bonus,
            "plants": {pid: p.to_dict() for pid, p in self.plants.items()},
            "pot_assignments": list(self.pot_assignments),
            "owned_upgrades": list(self.owned_upgrades),
            "collection": self.collection.to_dict(),
            "messages": list(self.messages[-40:]),
            "last_contest": self.last_contest,
            "rng_seed": self.rng_seed,
            "rng_state": self._rng.getstate()[1],  # not fully portable; also store seed counter
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.to_dict()
        # Store a simple rng advance counter via seed re-hash isn't perfect;
        # persist python random state as list
        state = self._rng.getstate()
        data["rng_fullstate"] = [state[0], list(state[1]), state[2]]
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> "GameState":
        data = json.loads(path.read_text())
        plants = {pid: Plant.from_dict(pdata) for pid, pdata in data.get("plants", {}).items()}
        gs = cls(
            money=data.get("money", 100),
            prestige=data.get("prestige", 0),
            day=data.get("day", 1),
            greenhouse_slots=data.get("greenhouse_slots", 6),
            grow_speed_bonus=data.get("grow_speed_bonus", 0),
            litter_bonus=data.get("litter_bonus", 0),
            plants=plants,
            pot_assignments=list(data.get("pot_assignments", [None] * 6)),
            owned_upgrades=list(data.get("owned_upgrades", [])),
            collection=CollectionLog.from_dict(data.get("collection", {})),
            messages=list(data.get("messages", [])),
            last_contest=data.get("last_contest"),
            rng_seed=data.get("rng_seed", 42),
        )
        full = data.get("rng_fullstate")
        if full:
            gs._rng.setstate((full[0], tuple(full[1]), full[2]))
        # Ensure pot list matches slots
        while len(gs.pot_assignments) < gs.greenhouse_slots:
            gs.pot_assignments.append(None)
        return gs

    @classmethod
    def new_game(cls, seed: Optional[int] = None) -> "GameState":
        seed = seed if seed is not None else random.randint(1, 999999)
        gs = cls(rng_seed=seed)
        gs._rng = random.Random(seed)
        gs.log("Welcome to Lovely Flowers — a dangerously serious plant-breeding greenhouse.")
        gs.log("Buy a seed, grow it, inspect it, then breed something stranger.")
        # Starter plant
        starter = create_seed_plant("Mavis", rng=gs._rng, quality="common")
        starter.planted = True
        starter.mature = True
        starter.growth_progress = 1.0
        starter.age_days = starter.phenotype().maturity_days
        gs.plants[starter.id] = starter
        gs.pot_assignments[0] = starter.id
        gs.collection.plants_owned_total = 1
        gs.collection.discover_from_plant(starter)
        gs.log(f"Your first plant, {starter.name}, is already mature. Don't get attached. (You will.)")
        return gs


SAVE_PATH = Path(__file__).resolve().parent.parent / "data" / "save.json"

"""Simple plant competitions — the racing equivalent."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from genetics.mutations import MUTATION_CATALOG
from genetics.plant import Plant


@dataclass(frozen=True)
class Competition:
    id: str
    name: str
    tagline: str
    category: str  # flower, giant, speed, abomination, people
    entry_fee: int
    prestige_required: int
    purse: Tuple[int, int, int]  # 1st, 2nd, 3rd
    prestige_reward: Tuple[int, int, int]


COMPETITIONS: List[Competition] = [
    Competition(
        id="peoples_pot",
        name="People's Pot",
        tagline="A friendly free-for-all for interesting specimens.",
        category="people",
        entry_fee=5,
        prestige_required=0,
        purse=(40, 20, 10),
        prestige_reward=(3, 2, 1),
    ),
    Competition(
        id="grand_flower",
        name="Grand Flower Show",
        tagline="Beauty, colour, symmetry, and floriferous excess.",
        category="flower",
        entry_fee=15,
        prestige_required=5,
        purse=(90, 45, 20),
        prestige_reward=(8, 4, 2),
    ),
    Competition(
        id="giants_cup",
        name="Giant's Cup",
        tagline="Size, yield, and the courage to stand upright.",
        category="giant",
        entry_fee=15,
        prestige_required=5,
        purse=(90, 45, 20),
        prestige_reward=(8, 4, 2),
    ),
    Competition(
        id="speed_grow",
        name="Speed Grow Championship",
        tagline="From seed to spectacle before lunch.",
        category="speed",
        entry_fee=20,
        prestige_required=12,
        purse=(110, 55, 25),
        prestige_reward=(10, 5, 2),
    ),
    Competition(
        id="abomination",
        name="Botanical Abomination",
        tagline="Rare mutations and genetics polite society rejects.",
        category="abomination",
        entry_fee=25,
        prestige_required=18,
        purse=(140, 70, 30),
        prestige_reward=(14, 7, 3),
    ),
]


# Cheap keep-vs-sell evaluations — Horsey "test race" equivalent
@dataclass(frozen=True)
class TrialShow:
    id: str
    name: str
    tagline: str
    category: str
    fee: int
    # Tiny purse; the point is the report card


TRIALS: List[TrialShow] = [
    TrialShow(
        id="trial_general",
        name="Potting Bench Trial",
        tagline="Quick all-rounder read. Keep or compost?",
        category="people",
        fee=2,
    ),
    TrialShow(
        id="trial_flower",
        name="Bloom Sniff Test",
        tagline="Beauty check without the big-show nerves.",
        category="flower",
        fee=3,
    ),
    TrialShow(
        id="trial_giant",
        name="Yardstick Trial",
        tagline="How big is big, really?",
        category="giant",
        fee=3,
    ),
    TrialShow(
        id="trial_speed",
        name="Stopwatch Sprout",
        tagline="Is it actually fast, or just anxious?",
        category="speed",
        fee=3,
    ),
    TrialShow(
        id="trial_weird",
        name="Oddity Peek",
        tagline="Rate the strangeness before the Abomination board laughs.",
        category="abomination",
        fee=4,
    ),
]


def get_trial(trial_id: str) -> TrialShow:
    for t in TRIALS:
        if t.id == trial_id:
            return t
    raise KeyError(trial_id)


def _grade(score: float, field_avg: float) -> str:
    ratio = score / max(field_avg, 1.0)
    if ratio >= 1.35:
        return "S"
    if ratio >= 1.15:
        return "A"
    if ratio >= 0.95:
        return "B"
    if ratio >= 0.75:
        return "C"
    if ratio >= 0.55:
        return "D"
    return "F"


@dataclass
class TrialResult:
    trial_id: str
    trial_name: str
    plant_id: str
    plant_name: str
    category: str
    score: float
    grade: str
    advice: str
    category_scores: Dict[str, str]
    fee_paid: int

    def to_dict(self) -> Dict:
        return {
            "trial_id": self.trial_id,
            "trial_name": self.trial_name,
            "plant_id": self.plant_id,
            "plant_name": self.plant_name,
            "category": self.category,
            "score": self.score,
            "grade": self.grade,
            "advice": self.advice,
            "category_scores": dict(self.category_scores),
            "fee_paid": self.fee_paid,
            "place": {"S": 1, "A": 1, "B": 2, "C": 3, "D": 4, "F": 5}.get(self.grade, 5),
            "ribbon": f"Trial {self.grade}",
            "competition_name": self.trial_name,
            "prize": 0,
            "prestige": 0,
        }


def run_trial(
    trial: TrialShow,
    plant: Plant,
    rng: Optional[random.Random] = None,
) -> TrialResult:
    """Cheap evaluation — report card across categories so you know keep vs sell."""
    rng = rng or random.Random()
    categories = ["flower", "giant", "speed", "abomination", "people"]
    grades: Dict[str, str] = {}
    scores: Dict[str, float] = {}
    for cat in categories:
        s = score_plant(plant, cat)
        # Fake a local field average for grading
        field = 55 + rng.uniform(-8, 12)
        grades[cat] = _grade(s, field)
        scores[cat] = s

    focus = score_plant(plant, trial.category)
    field = 55 + rng.uniform(-8, 12)
    grade = _grade(focus, field)

    advice_map = {
        "S": "Keep. This one has a future. Possibly a terrifying one.",
        "A": "Strong keeper. Worth breeding from.",
        "B": "Decent. Useful parent or solid mid-show entry.",
        "C": "Average. Sell if pots are tight; keep if it carries something hidden.",
        "D": "Weak specimen. Sell unless it's a mutation carrier.",
        "F": "Compost candidate. Or radiation chamber volunteer.",
    }
    # Carrier hint
    ph = plant.phenotype()
    if grade in ("D", "F") and ph.carrier_mutations:
        advice = "Looks useless — but it may carry hidden genetics. Check carefully before selling."
    elif plant.species_kind != "plant" and grade in ("A", "S", "B"):
        advice = advice_map[grade] + " Also: it isn't strictly a plant. Judges will notice."
    else:
        advice = advice_map[grade]

    return TrialResult(
        trial_id=trial.id,
        trial_name=trial.name,
        plant_id=plant.id,
        plant_name=plant.name,
        category=trial.category,
        score=round(focus, 1),
        grade=grade,
        advice=advice,
        category_scores=grades,
        fee_paid=trial.fee,
    )


def get_competition(comp_id: str) -> Competition:
    for c in COMPETITIONS:
        if c.id == comp_id:
            return c
    raise KeyError(comp_id)


def score_plant(plant: Plant, category: str) -> float:
    """Evaluate a plant for a competition category."""
    ph = plant.phenotype()
    base = {
        "flower": ph.beauty * 100
        + ph.flower * 40
        + ph.symmetry * 35
        + ph.quality * 25
        + _colour_bonus(ph.colour_id),
        "giant": ph.size_score * 100
        + ph.height * 40
        + ph.yield_ * 35
        + ph.stem * 30,
        "speed": ph.speed_score * 100
        + ph.growth * 50
        + max(0, 25 - ph.maturity_days) * 3,
        "abomination": ph.strangeness * 90
        + len(ph.expressed_mutations) * 18
        + sum(
            (0.05 / max(MUTATION_CATALOG[m].rarity, 0.005))
            for m in ph.expressed_mutations
        ),
        "people": (
            ph.beauty * 35
            + ph.size_score * 25
            + ph.speed_score * 20
            + ph.strangeness * 40
            + ph.quality * 20
            + len(ph.expressed_mutations) * 8
        ),
    }[category]

    # Mutation contest bonuses
    for mid in ph.expressed_mutations:
        base += MUTATION_CATALOG[mid].contest_bonus.get(category, 0)

    # Slight generation prestige — long bloodlines impress
    base += min(15, plant.generation * 0.4)
    return base


def _colour_bonus(colour_id: str) -> float:
    return {
        "c_green": 0,
        "c_yellow": 4,
        "c_orange": 5,
        "c_red": 6,
        "c_pink": 7,
        "c_purple": 9,
        "c_blue": 10,
        "c_white": 8,
        "c_black": 12,
    }.get(colour_id, 0)


def _npc_score(category: str, prestige: int, rng: random.Random) -> float:
    """Generate a field of NPC competitors scaled to player prestige."""
    tier = 40 + prestige * 1.8 + rng.uniform(-15, 25)
    # Category flavour
    tier *= {
        "flower": rng.uniform(0.85, 1.15),
        "giant": rng.uniform(0.85, 1.15),
        "speed": rng.uniform(0.9, 1.2),
        "abomination": rng.uniform(0.7, 1.25),
        "people": rng.uniform(0.9, 1.1),
    }[category]
    return max(10.0, tier)


@dataclass
class ContestResult:
    competition_id: str
    competition_name: str
    plant_id: str
    plant_name: str
    place: int
    field_size: int
    score: float
    prize: int
    prestige: int
    ribbon: str
    summary: str

    def to_dict(self) -> Dict:
        return {
            "competition_id": self.competition_id,
            "competition_name": self.competition_name,
            "plant_id": self.plant_id,
            "plant_name": self.plant_name,
            "place": self.place,
            "field_size": self.field_size,
            "score": self.score,
            "prize": self.prize,
            "prestige": self.prestige,
            "ribbon": self.ribbon,
            "summary": self.summary,
        }


def run_competition(
    competition: Competition,
    plant: Plant,
    player_prestige: int,
    rng: Optional[random.Random] = None,
) -> ContestResult:
    rng = rng or random.Random()
    player_score = score_plant(plant, competition.category)
    field_size = rng.randint(6, 10)
    npc_scores = [
        _npc_score(competition.category, player_prestige, rng)
        for _ in range(field_size - 1)
    ]
    better = sum(1 for s in npc_scores if s > player_score)
    place = better + 1

    prize = 0
    prestige = 0
    if place == 1:
        prize, prestige = competition.purse[0], competition.prestige_reward[0]
        ribbon = "Gold"
    elif place == 2:
        prize, prestige = competition.purse[1], competition.prestige_reward[1]
        ribbon = "Silver"
    elif place == 3:
        prize, prestige = competition.purse[2], competition.prestige_reward[2]
        ribbon = "Bronze"
    else:
        ribbon = "Participant"
        prestige = 0

    summaries = {
        1: f"{plant.name} stunned the judges. First place!",
        2: f"{plant.name} nearly took the cup — second place.",
        3: f"{plant.name} earned a respectable third.",
    }
    summary = summaries.get(
        place,
        f"{plant.name} placed {place}{'_th' if place > 3 else ''} of {field_size}. Back to the breeding bench.",
    )
    # Fix ordinal in fallback
    if place > 3:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(place % 10, "th")
        if 10 < place % 100 < 14:
            suffix = "th"
        summary = f"{plant.name} placed {place}{suffix} of {field_size}. Back to the breeding bench."

    return ContestResult(
        competition_id=competition.id,
        competition_name=competition.name,
        plant_id=plant.id,
        plant_name=plant.name,
        place=place,
        field_size=field_size,
        score=round(player_score, 1),
        prize=prize,
        prestige=prestige,
        ribbon=ribbon,
        summary=summary,
    )

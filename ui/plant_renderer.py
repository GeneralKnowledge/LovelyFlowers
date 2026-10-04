"""Plant visuals — facade over hybrid sine morph renderer."""

from __future__ import annotations

from typing import Dict, Tuple

import pygame

from genetics.plant import Plant
from procgen.draw_pygame import draw_morph_plant, draw_seed
from procgen.morph import morph_from_phenotype, seed_from_plant_id

# Portrait cache with coarse sway buckets (Phase 5 polish)
_cache: Dict[Tuple[str, int, int, int], pygame.Surface] = {}
_CACHE_LIMIT = 64


def clear_plant_cache() -> None:
    _cache.clear()


def _maturity_bucket(progress: float) -> int:
    return int(max(0.0, min(1.0, progress)) * 10)


def draw_plant(
    surface: pygame.Surface,
    plant: Plant,
    center: Tuple[int, int],
    max_height: int,
    time_s: float = 0.0,
    seedling: bool = False,
) -> None:
    """Draw a plant whose silhouette reflects genetics via morph params."""
    progress = 1.0 if plant.mature else max(0.12, plant.growth_progress)

    if seedling and not plant.mature and plant.growth_progress < 0.15:
        draw_seed(surface, center[0], center[1])
        return

    ph = plant.phenotype()
    morph = morph_from_phenotype(
        ph,
        seed=seed_from_plant_id(plant.id),
        label=plant.name,
        progress=progress,
    )
    draw_morph_plant(surface, morph, center, max_height, time_s=time_s, include_pot=True)


def plant_portrait(
    plant: Plant, size: int = 120, time_s: float = 0.0
) -> pygame.Surface:
    key = (
        plant.id,
        size,
        _maturity_bucket(1.0 if plant.mature else plant.growth_progress),
        int(time_s * 4) % 8,
    )
    cached = _cache.get(key)
    if cached is not None:
        return cached

    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (60, 90, 55, 40), (10, size - 36, size - 20, 28))
    draw_plant(surf, plant, (size // 2, size - 24), int(size * 0.7), time_s=time_s)
    if len(_cache) >= _CACHE_LIMIT:
        _cache.pop(next(iter(_cache)))
    _cache[key] = surf
    return surf

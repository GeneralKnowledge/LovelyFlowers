"""Shape builders built on wave primitives (leaf / petal outlines)."""

from __future__ import annotations

from typing import List, Sequence, Tuple

from procgen.waves import sample_leaf_polygon, sample_petal_polygon

Point = Tuple[float, float]


def leaf_outline(
    length: float,
    width: float,
    curl: float = 0.0,
    serration: float = 0.0,
    steps: int = 14,
) -> List[Point]:
    return sample_leaf_polygon(length, width, curl=curl, serration=serration, steps=steps)


def flower_outline(
    radius: float,
    petals: int,
    lobe_amp: float = 0.35,
    phase: float = 0.0,
    steps_per_petal: int = 8,
) -> List[Point]:
    return sample_petal_polygon(
        radius, petals, lobe_amp=lobe_amp, phase=phase, steps_per_petal=steps_per_petal
    )


SHAPE_PETALS = {
    "sh_round": 6,
    "sh_star": 5,
    "sh_trumpet": 4,
    "sh_spike": 3,
    "sh_bell": 5,
    "sh_flat": 8,
}


def petals_for_shape(shape_id: str) -> int:
    return SHAPE_PETALS.get(shape_id, 5)

"""Pygame drawing for PlantScene / MorphParams."""

from __future__ import annotations

from typing import Tuple

import pygame

from procgen.morph import MorphParams
from procgen.plant_scene import PlantScene, build_scene

POT = (148, 98, 62)
POT_DARK = (112, 72, 46)
SOIL = (72, 52, 34)


def draw_pot(surface: pygame.Surface, cx: int, cy: int) -> None:
    rect = pygame.Rect(cx - 18, cy - 4, 36, 20)
    pygame.draw.rect(surface, POT, rect, border_radius=3)
    pygame.draw.rect(surface, POT_DARK, rect.inflate(-6, -8).move(0, 3), border_radius=2)
    pygame.draw.ellipse(surface, SOIL, (cx - 14, cy - 9, 28, 9))


def draw_seed(surface: pygame.Surface, cx: int, cy: int) -> None:
    pygame.draw.rect(surface, POT, (cx - 14, cy - 6, 28, 16), border_radius=3)
    pygame.draw.ellipse(surface, (90, 60, 30), (cx - 5, cy - 10, 10, 8))


def draw_scene(surface: pygame.Surface, scene: PlantScene) -> None:
    if scene.draw_pot:
        draw_pot(surface, scene.pot_center[0], scene.pot_center[1])

    for poly in scene.polygons:
        if len(poly.points) >= 3:
            pygame.draw.polygon(surface, poly.colour, poly.points)
            if poly.edge:
                pygame.draw.polygon(surface, poly.edge, poly.points, 1)

    for line in scene.polylines:
        if len(line.points) >= 2:
            pygame.draw.lines(surface, line.colour, False, line.points, line.width)
            if line.highlight:
                pygame.draw.lines(
                    surface, line.highlight, False, line.points, max(1, line.width - 2)
                )

    for circle in scene.circles:
        cx, cy = int(circle.center[0]), int(circle.center[1])
        r = max(1, int(round(circle.radius)))
        if circle.alpha is not None:
            side = r * 2 + 4
            glow = pygame.Surface((side, side), pygame.SRCALPHA)
            col = (*circle.colour[:3], circle.alpha)
            pygame.draw.circle(glow, col, (side // 2, side // 2), r)
            surface.blit(glow, (cx - side // 2, cy - side // 2))
        else:
            pygame.draw.circle(surface, circle.colour, (cx, cy), r, circle.width)


def draw_morph_plant(
    surface: pygame.Surface,
    morph: MorphParams,
    center: Tuple[int, int],
    max_height: int,
    time_s: float = 0.0,
    include_pot: bool = True,
) -> None:
    """Build scene from morph and draw it."""
    scene = build_scene(morph, center, max_height, time_s=time_s, include_pot=include_pot)
    draw_scene(surface, scene)

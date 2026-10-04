"""Procedural plant visuals driven by phenotype traits and mutations."""

from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple

import pygame

from genetics.mutations import MUTATION_CATALOG
from genetics.plant import Plant


def draw_plant(
    surface: pygame.Surface,
    plant: Plant,
    center: Tuple[int, int],
    max_height: int,
    time_s: float = 0.0,
    seedling: bool = False,
) -> None:
    """Draw a plant whose silhouette reflects genetics."""
    ph = plant.phenotype()
    cx, cy = center
    progress = 1.0 if plant.mature else max(0.12, plant.growth_progress)

    if seedling and not plant.mature and plant.growth_progress < 0.15:
        _draw_seed(surface, cx, cy)
        return

    h = int(max_height * (0.35 + 0.65 * min(ph.height, 1.2)) * progress)
    stem_w = max(2, int(3 + ph.stem * 5 + ph.width * 2))
    sway = math.sin(time_s * 2.2 + hash(plant.id) % 7) * (2.5 + (1.1 - ph.stem) * 3)

    # Pot
    pot_rect = pygame.Rect(cx - 18, cy - 8, 36, 20)
    pygame.draw.rect(surface, (140, 90, 60), pot_rect, border_radius=3)
    pygame.draw.rect(surface, (110, 70, 45), pot_rect.inflate(-6, -10).move(0, 4), border_radius=2)

    soil_y = cy - 8
    mutations = set(ph.expressed_mutations)

    # Walking roots
    if "walking_roots" in mutations:
        for i, side in enumerate((-1, 1, -1, 1)):
            rx = cx + side * (10 + i * 5)
            ry = cy + 6 + (i % 2) * 3
            pygame.draw.ellipse(surface, (90, 70, 50), (rx - 4, ry - 3, 8, 12))
            pygame.draw.circle(surface, (60, 45, 35), (rx, ry + 8), 3)

    # Multi-stem or normal stem(s)
    stem_count = 1
    if "multi_stem" in mutations:
        stem_count = 2 + int(ph.branch * 2)
    elif ph.branch > 0.7:
        stem_count = 2

    stem_color = (50, 110, 55)
    if "glass_stem" in mutations:
        stem_color = (140, 200, 180)
    if "spiral_growth" in mutations:
        _draw_spiral_stem(surface, cx, soil_y, h, stem_w, stem_color, sway, time_s)
        stem_tops = [(int(cx + sway), soil_y - h)]
    else:
        stem_tops = []
        for i in range(stem_count):
            offset = (i - (stem_count - 1) / 2) * (8 + ph.width * 6)
            top = _draw_stem(
                surface,
                cx + offset,
                soil_y,
                h,
                stem_w,
                stem_color,
                sway * (1 - i * 0.15),
                branchiness=ph.branch,
            )
            stem_tops.append(top)

    # Leaves
    leaf_count = 2 + int(ph.leaf * 5 + ph.branch * 3)
    if "giant_leaves" in mutations:
        leaf_count = max(leaf_count, 4)
    leaf_scale = 0.7 + ph.leaf * 0.9
    if "giant_leaves" in mutations:
        leaf_scale *= 1.55
    feather = "feather_leaves" in mutations

    rng = random.Random(hash(plant.id) & 0xFFFFFFFF)
    for i in range(leaf_count):
        t = (i + 1) / (leaf_count + 1)
        base_x = cx + sway * t
        base_y = soil_y - int(h * t * 0.85)
        side = 1 if i % 2 == 0 else -1
        angle = side * (25 + ph.branch * 25) + rng.uniform(-8, 8)
        _draw_leaf(
            surface,
            (base_x, base_y),
            angle,
            leaf_scale * (0.7 + progress * 0.3),
            feather=feather,
            color=_leaf_color(ph.disease, mutations),
        )

    # Flowers
    bloom_count = int(ph.flower * 6 * progress)
    if "dense_bloom" in mutations:
        bloom_count = int(bloom_count * 1.6) + 2
    bloom_count = max(0, min(14, bloom_count))
    glow = "bioluminescence" in mutations
    face = "face_bloom" in mutations
    eyes = "eye_structures" in mutations
    rainbow = "rainbow_shift" in mutations

    for i, (tx, ty) in enumerate(stem_tops):
        local = max(1, bloom_count // max(1, len(stem_tops)))
        for j in range(local):
            fx = tx + rng.randint(-10, 10) * (0.5 + ph.branch)
            fy = ty + rng.randint(-6, 8) - j * 3
            color = ph.colour_rgb
            if rainbow:
                phase = time_s * 2 + i + j
                color = (
                    int(128 + 127 * math.sin(phase)),
                    int(128 + 127 * math.sin(phase + 2)),
                    int(128 + 127 * math.sin(phase + 4)),
                )
            _draw_flower(
                surface,
                (int(fx), int(fy)),
                ph.shape_id,
                color,
                scale=0.7 + ph.flower * 0.5 + ph.quality * 0.2,
                glow=glow,
                face=face,
                eyes=eyes,
                time_s=time_s,
            )

    # Sonic bloom rings
    if "thunder_bloom" in mutations and plant.mature:
        pulse = 0.5 + 0.5 * math.sin(time_s * 5)
        if stem_tops:
            pygame.draw.circle(
                surface,
                (220, 220, 100),
                stem_tops[0],
                int(12 + pulse * 10),
                1,
            )


def _draw_seed(surface: pygame.Surface, cx: int, cy: int) -> None:
    pygame.draw.rect(surface, (140, 90, 60), (cx - 14, cy - 6, 28, 16), border_radius=3)
    pygame.draw.ellipse(surface, (90, 60, 30), (cx - 5, cy - 10, 10, 8))


def _draw_stem(
    surface: pygame.Surface,
    x: float,
    base_y: int,
    h: int,
    w: int,
    color: Tuple[int, int, int],
    sway: float,
    branchiness: float,
) -> Tuple[int, int]:
    points: List[Tuple[int, int]] = []
    steps = max(6, h // 8)
    for i in range(steps + 1):
        t = i / steps
        px = int(x + sway * t * t)
        py = int(base_y - h * t)
        points.append((px, py))
        if branchiness > 0.55 and 0.3 < t < 0.85 and i % 3 == 0:
            bx = px + int((1 if i % 2 == 0 else -1) * (8 + branchiness * 12))
            by = py + 4
            pygame.draw.line(surface, color, (px, py), (bx, by), max(1, w - 1))
    if len(points) >= 2:
        pygame.draw.lines(surface, color, False, points, w)
    return points[-1]


def _draw_spiral_stem(
    surface: pygame.Surface,
    x: float,
    base_y: int,
    h: int,
    w: int,
    color: Tuple[int, int, int],
    sway: float,
    time_s: float,
) -> None:
    points = []
    steps = max(10, h // 5)
    for i in range(steps + 1):
        t = i / steps
        ang = t * math.pi * 3 + time_s * 0.5
        px = int(x + math.cos(ang) * (6 + t * 8) + sway * t)
        py = int(base_y - h * t)
        points.append((px, py))
    if len(points) >= 2:
        pygame.draw.lines(surface, color, False, points, w)


def _leaf_color(disease: float, mutations: set) -> Tuple[int, int, int]:
    g = int(80 + disease * 80)
    if "feather_leaves" in mutations:
        return (70, g, 90)
    return (40, g, 50)


def _draw_leaf(
    surface: pygame.Surface,
    origin: Tuple[float, float],
    angle_deg: float,
    scale: float,
    feather: bool,
    color: Tuple[int, int, int],
) -> None:
    ang = math.radians(angle_deg)
    length = 14 * scale
    width = 7 * scale
    ox, oy = origin
    tip = (ox + math.cos(ang) * length, oy + math.sin(ang) * length)
    left = (
        ox + math.cos(ang + 0.6) * width,
        oy + math.sin(ang + 0.6) * width,
    )
    right = (
        ox + math.cos(ang - 0.6) * width,
        oy + math.sin(ang - 0.6) * width,
    )
    pygame.draw.polygon(surface, color, [(ox, oy), left, tip, right])
    if feather:
        for i in range(3):
            t = 0.3 + i * 0.2
            fx = ox + (tip[0] - ox) * t
            fy = oy + (tip[1] - oy) * t
            pygame.draw.line(
                surface,
                (color[0] + 20, min(255, color[1] + 20), color[2] + 20),
                (fx, fy),
                (fx + math.cos(ang + 1.2) * 5, fy + math.sin(ang + 1.2) * 5),
                1,
            )


def _draw_flower(
    surface: pygame.Surface,
    pos: Tuple[int, int],
    shape_id: str,
    color: Tuple[int, int, int],
    scale: float,
    glow: bool,
    face: bool,
    eyes: bool,
    time_s: float,
) -> None:
    x, y = pos
    r = max(4, int(6 * scale))
    if glow:
        glow_col = (min(255, color[0] + 40), min(255, color[1] + 60), min(255, color[2] + 80))
        s = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*glow_col, 60), (r * 2, r * 2), r * 2)
        surface.blit(s, (x - r * 2, y - r * 2))

    petals = {
        "sh_round": 6,
        "sh_star": 5,
        "sh_trumpet": 4,
        "sh_spike": 3,
        "sh_bell": 5,
        "sh_flat": 8,
    }.get(shape_id, 6)

    for i in range(petals):
        ang = (math.pi * 2 * i) / petals + time_s * 0.2
        if shape_id == "sh_star":
            px = x + int(math.cos(ang) * r)
            py = y + int(math.sin(ang) * r)
            pygame.draw.polygon(
                surface,
                color,
                [
                    (x, y),
                    (px + int(math.cos(ang + 0.4) * r * 0.4), py + int(math.sin(ang + 0.4) * r * 0.4)),
                    (x + int(math.cos(ang) * r * 1.4), y + int(math.sin(ang) * r * 1.4)),
                    (px + int(math.cos(ang - 0.4) * r * 0.4), py + int(math.sin(ang - 0.4) * r * 0.4)),
                ],
            )
        elif shape_id == "sh_spike":
            pygame.draw.ellipse(
                surface,
                color,
                (x + int(math.cos(ang) * r * 0.3) - 2, y + int(math.sin(ang) * r) - r, 4, r * 2),
            )
        else:
            px = x + int(math.cos(ang) * r * 0.7)
            py = y + int(math.sin(ang) * r * 0.7)
            pygame.draw.circle(surface, color, (px, py), max(2, r // 2))

    center_col = (240, 220, 80) if not eyes else (30, 30, 30)
    pygame.draw.circle(surface, center_col, (x, y), max(2, r // 3))

    if eyes:
        pygame.draw.circle(surface, (240, 240, 240), (x - 2, y - 1), 2)
        pygame.draw.circle(surface, (240, 240, 240), (x + 2, y - 1), 2)
        pygame.draw.circle(surface, (20, 20, 20), (x - 2, y - 1), 1)
        pygame.draw.circle(surface, (20, 20, 20), (x + 2, y - 1), 1)

    if face:
        pygame.draw.circle(surface, (20, 20, 20), (x - 3, y - 1), 1)
        pygame.draw.circle(surface, (20, 20, 20), (x + 3, y - 1), 1)
        pygame.draw.arc(surface, (20, 20, 20), (x - 4, y, 8, 5), 3.4, 6.0, 1)


def plant_portrait(
    plant: Plant, size: int = 120, time_s: float = 0.0
) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    # soft ground wash
    pygame.draw.ellipse(surf, (60, 90, 55, 40), (10, size - 36, size - 20, 28))
    draw_plant(surf, plant, (size // 2, size - 24), int(size * 0.7), time_s=time_s)
    return surf

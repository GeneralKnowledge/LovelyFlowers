"""Plant scene graph — geometry parts built from MorphParams (pygame-agnostic)."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from procgen.morph import MorphParams
from procgen.shapes import flower_outline, leaf_outline
from procgen.waves import sample_stem_curve

Point = Tuple[float, float]
Colour = Tuple[int, int, int]


@dataclass
class Polyline:
    points: List[Point]
    colour: Colour
    width: int = 2
    highlight: Optional[Colour] = None


@dataclass
class Polygon:
    points: List[Point]
    colour: Colour
    edge: Optional[Colour] = None


@dataclass
class Circle:
    center: Point
    radius: float
    colour: Colour
    width: int = 0  # 0 = filled
    alpha: Optional[int] = None


@dataclass
class PlantScene:
    """Drawable parts for one plant. Coordinates are screen-space."""

    polylines: List[Polyline] = field(default_factory=list)
    polygons: List[Polygon] = field(default_factory=list)
    circles: List[Circle] = field(default_factory=list)
    pot_center: Tuple[int, int] = (0, 0)
    draw_pot: bool = True


def _stem_curve(
    morph: MorphParams,
    length: float,
    amp: float,
    phase: float,
    lean: float,
    time_s: float,
) -> List[Point]:
    freq = morph.stem_freq
    harmonics = list(morph.harmonics)
    if morph.spiral:
        freq = 1.6 + morph.stem_freq * 0.35
        harmonics = [(2.0, 0.2)]
        amp = amp * 1.15
        phase = phase + time_s * 0.4
    return sample_stem_curve(
        length=length,
        amp=amp,
        freq=freq,
        phase=phase,
        harmonics=harmonics,
        steps=max(18, int(length // 4)),
        lean=lean,
    )


def build_scene(
    morph: MorphParams,
    center: Tuple[int, int],
    max_height: int,
    time_s: float = 0.0,
    include_pot: bool = True,
) -> PlantScene:
    """Turn MorphParams into screen-space geometry."""
    cx, cy = center
    rng = random.Random(morph.seed)
    progress = max(0.12, min(1.0, morph.progress))
    length = max_height * (0.42 + 0.58 * morph.height) * progress
    amp = max_height * (0.04 + morph.stem_amp * 0.22)
    if morph.spiral:
        amp = max(amp, max_height * 0.08)
    stem_w = max(2, int(3 + morph.stem_width * 3.5))
    if morph.glass_stem:
        stem_w = max(2, stem_w - 1)
    stem_colour = morph.stem_colour
    sway = math.sin(time_s * 1.8 + morph.stem_phase) * (1.5 + morph.stem_amp * 5)

    scene = PlantScene(pot_center=(cx, cy), draw_pot=include_pot)
    soil_y = cy - 8

    if morph.walking_roots:
        for i, side in enumerate((-1, 1, -1, 1)):
            rx = cx + side * (12 + i * 4)
            ry = cy + 10 + (i % 2) * 2
            scene.circles.append(Circle((rx, ry + 2), 5, (96, 74, 52)))
            scene.circles.append(Circle((rx, ry + 8), 3, (58, 42, 30)))

    stem_tops: List[Tuple[int, int]] = []
    stem_paths: List[List[Tuple[int, int]]] = []
    stem_count = max(1, morph.stem_count)

    for s_i in range(stem_count):
        x_off = (s_i - (stem_count - 1) / 2) * (12 + morph.branch_spread * 10)
        phase = morph.stem_phase + s_i * 0.85
        curve = _stem_curve(
            morph,
            length=length * (1.0 - 0.08 * s_i),
            amp=amp,
            phase=phase,
            lean=morph.lean + x_off * 0.02,
            time_s=time_s,
        )
        pts = [
            (int(cx + x + x_off + sway * (i / max(1, len(curve) - 1))), int(soil_y + y))
            for i, (x, y) in enumerate(curve)
        ]
        hi = None
        if morph.glass_stem:
            hi = (
                min(255, stem_colour[0] + 70),
                min(255, stem_colour[1] + 50),
                min(255, stem_colour[2] + 40),
            )
        if len(pts) >= 2:
            scene.polylines.append(Polyline(pts, stem_colour, stem_w, highlight=hi))
        stem_tops.append(pts[-1])
        stem_paths.append(pts)

        branch_n = min(morph.branch_count, 3 if stem_count == 1 else 2)
        for b in range(branch_n):
            if len(pts) < 4:
                break
            t = 0.4 + 0.4 * ((b + 1) / (branch_n + 1))
            idx = min(len(pts) - 2, max(2, int(t * (len(pts) - 1))))
            bx, by = pts[idx]
            side = 1 if (b + s_i) % 2 == 0 else -1
            ang = side * (0.75 + morph.branch_spread * 0.55) + rng.uniform(-0.12, 0.12)
            blen = length * (0.22 + 0.08 * rng.random())
            bpts = []
            for i in range(11):
                tt = i / 10
                wave = amp * 0.25 * math.sin(2 * math.pi * 1.4 * tt + phase + b)
                bpts.append(
                    (
                        int(bx + math.cos(ang) * blen * tt + math.cos(ang + math.pi / 2) * wave),
                        int(by + math.sin(ang) * blen * tt + math.sin(ang + math.pi / 2) * wave),
                    )
                )
            scene.polylines.append(Polyline(bpts, stem_colour, max(2, stem_w - 1)))

    main = stem_paths[0] if stem_paths else []
    leaf_n = max(1, int(morph.leaf_count * (0.4 + 0.6 * progress)))
    leaf_len = morph.leaf_length * max_height * (0.22 if not morph.giant_leaves else 0.3) * progress
    leaf_w = leaf_len * (0.5 if not morph.giant_leaves else 0.72)

    for i in range(leaf_n):
        if len(main) < 3:
            break
        t = 0.2 + 0.65 * ((i + 1) / (leaf_n + 1))
        idx = min(len(main) - 1, int(t * (len(main) - 1)))
        ax, ay = main[idx]
        side = 1 if i % 2 == 0 else -1
        ang = side * (0.95 + morph.branch_spread * 0.35) + rng.uniform(-0.15, 0.15)
        lpts = []
        for lx, ly in leaf_outline(
            length=leaf_len,
            width=leaf_w,
            curl=morph.leaf_curl * side * 0.7,
            serration=0.35 if morph.feather else 0.08,
            steps=14,
        ):
            px = ax + math.cos(ang) * (-ly) + math.cos(ang + math.pi / 2) * lx
            py = ay + math.sin(ang) * (-ly) + math.sin(ang + math.pi / 2) * lx
            lpts.append((int(px), int(py)))
        if len(lpts) >= 3:
            edge = (
                max(0, morph.leaf_colour[0] - 20),
                max(0, morph.leaf_colour[1] - 15),
                max(0, morph.leaf_colour[2] - 15),
            )
            scene.polygons.append(Polygon(lpts, morph.leaf_colour, edge=edge))
            if morph.feather:
                vein = (
                    min(255, morph.leaf_colour[0] + 18),
                    min(255, morph.leaf_colour[1] + 28),
                    min(255, morph.leaf_colour[2] + 12),
                )
                for k in range(4):
                    tt = 0.22 + k * 0.18
                    fx = ax + math.cos(ang) * leaf_len * tt
                    fy = ay + math.sin(ang) * leaf_len * tt
                    scene.polylines.append(
                        Polyline(
                            [
                                (int(fx), int(fy)),
                                (
                                    int(fx + math.cos(ang + 1.15) * leaf_w * 0.35),
                                    int(fy + math.sin(ang + 1.15) * leaf_w * 0.35),
                                ),
                            ],
                            vein,
                            1,
                        )
                    )

    bloom_scale = 0.35 + 0.65 * progress
    for fi, (tx, ty) in enumerate(stem_tops):
        local = max(1, (morph.flower_count + len(stem_tops) - 1) // max(1, len(stem_tops)))
        for j in range(local):
            fx = tx + int((j - (local - 1) / 2) * 10) + rng.randint(-2, 2)
            fy = ty - 4 - j * 5
            colour = morph.colour
            if morph.rainbow:
                phase = time_s * 1.5 + fi + j
                colour = (
                    int(140 + 90 * math.sin(phase)),
                    int(100 + 90 * math.sin(phase + 2.1)),
                    int(140 + 90 * math.sin(phase + 4.2)),
                )
            radius = max(6.0, morph.flower_radius * max_height * 0.13 * bloom_scale)
            if morph.glow:
                scene.circles.append(
                    Circle(
                        (fx, fy),
                        radius * 1.8,
                        (
                            min(255, colour[0] + 30),
                            min(255, colour[1] + 50),
                            min(255, colour[2] + 70),
                        ),
                        alpha=70,
                    )
                )
            petal = flower_outline(
                radius=radius,
                petals=morph.petals,
                lobe_amp=0.28 + morph.petal_amp * 0.25,
                phase=morph.stem_phase * 0.2,
                steps_per_petal=10,
            )
            ppts = [(int(fx + x), int(fy + y)) for x, y in petal]
            if len(ppts) >= 3:
                edge = (
                    max(0, colour[0] - 35),
                    max(0, colour[1] - 35),
                    max(0, colour[2] - 35),
                )
                scene.polygons.append(Polygon(ppts, colour, edge=edge))
            center_col = (36, 32, 28) if morph.eyes or morph.face else (245, 220, 95)
            scene.circles.append(Circle((fx, fy), max(3, int(radius * 0.28)), center_col))
            if morph.eyes:
                scene.circles.append(Circle((fx - 4, fy - 1), 3, (250, 250, 245)))
                scene.circles.append(Circle((fx + 4, fy - 1), 3, (250, 250, 245)))
                scene.circles.append(Circle((fx - 4, fy - 1), 1, (20, 20, 20)))
                scene.circles.append(Circle((fx + 4, fy - 1), 1, (20, 20, 20)))
            if morph.face:
                scene.circles.append(Circle((fx - 4, fy - 2), 1, (20, 20, 20)))
                scene.circles.append(Circle((fx + 4, fy - 2), 1, (20, 20, 20)))
                # smile approximated as small arc via thin circles along a curve
                for a in (3.6, 4.2, 4.8, 5.4):
                    sx = fx + math.cos(a) * 5
                    sy = fy + 2 + math.sin(a) * 3
                    scene.circles.append(Circle((sx, sy), 0.8, (20, 20, 20)))
            if morph.thunder and j == 0:
                pulse = 0.5 + 0.5 * math.sin(time_s * 4.5 + morph.stem_phase)
                scene.circles.append(
                    Circle((fx, fy), radius + 4 + pulse * 6, (235, 230, 120), width=1)
                )

    return scene

"""Pygame preview renderer for hybrid sine plants — standalone, not wired into the game UI."""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Optional, Tuple

import pygame

from procgen.morph import MorphParams, demo_catalog
from procgen.waves import sample_leaf_polygon, sample_petal_polygon, sample_stem_curve


BG = (24, 38, 32)
CARD = (36, 54, 46)
POT = (148, 98, 62)
POT_DARK = (112, 72, 46)
SOIL = (72, 52, 34)
INK = (232, 238, 224)
MUTED = (168, 188, 172)


def draw_pot(surface: pygame.Surface, cx: int, cy: int) -> None:
    rect = pygame.Rect(cx - 22, cy - 4, 44, 22)
    pygame.draw.rect(surface, POT, rect, border_radius=4)
    pygame.draw.rect(surface, POT_DARK, rect.inflate(-8, -10).move(0, 4), border_radius=3)
    pygame.draw.ellipse(surface, SOIL, (cx - 16, cy - 10, 32, 10))


def _stem_points(
    morph: MorphParams,
    length: float,
    amp: float,
    phase: float,
    lean: float,
    time_s: float,
) -> List[Tuple[float, float]]:
    freq = morph.stem_freq
    harmonics = list(morph.harmonics)
    if morph.spiral:
        # One coherent coil — not an ECG scribble
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


def draw_morph_plant(
    surface: pygame.Surface,
    morph: MorphParams,
    center: Tuple[int, int],
    max_height: int,
    time_s: float = 0.0,
) -> None:
    """Draw one hybrid plant: sine stems, hybrid leaves/flowers, simple ornaments."""
    cx, cy = center
    rng = random.Random(morph.seed)
    length = max_height * (0.42 + 0.58 * morph.height)
    amp = max_height * (0.04 + morph.stem_amp * 0.22)
    # Keep spirals readable as coils, not wild plots
    if morph.spiral:
        amp = max(amp, max_height * 0.08)
    stem_w = max(3, int(3 + morph.stem_width * 3.5))
    if morph.glass_stem:
        stem_w = max(2, stem_w - 1)
    stem_colour = morph.stem_colour
    sway = math.sin(time_s * 1.8 + morph.stem_phase) * (1.5 + morph.stem_amp * 5)

    draw_pot(surface, cx, cy)
    soil_y = cy - 8

    if morph.walking_roots:
        for i, side in enumerate((-1, 1, -1, 1)):
            rx = cx + side * (12 + i * 4)
            ry = cy + 10 + (i % 2) * 2
            pygame.draw.ellipse(surface, (96, 74, 52), (rx - 4, ry - 4, 9, 13))
            pygame.draw.circle(surface, (58, 42, 30), (rx, ry + 8), 3)

    stem_tops: List[Tuple[int, int]] = []
    stem_paths: List[List[Tuple[int, int]]] = []
    stem_count = max(1, morph.stem_count)

    for s_i in range(stem_count):
        x_off = (s_i - (stem_count - 1) / 2) * (12 + morph.branch_spread * 10)
        phase = morph.stem_phase + s_i * 0.85
        curve = _stem_points(
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
        if len(pts) >= 2:
            pygame.draw.lines(surface, stem_colour, False, pts, stem_w)
            if morph.glass_stem:
                hi = (min(255, stem_colour[0] + 70), min(255, stem_colour[1] + 50), min(255, stem_colour[2] + 40))
                pygame.draw.lines(surface, hi, False, pts, max(1, stem_w - 2))
        stem_tops.append(pts[-1])
        stem_paths.append(pts)

        # Side branches: short sine segments, limited count for clarity
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
            pygame.draw.lines(surface, stem_colour, False, bpts, max(2, stem_w - 1))

    # Leaves along primary stem
    main = stem_paths[0] if stem_paths else []
    leaf_n = morph.leaf_count
    leaf_len = morph.leaf_length * max_height * (0.22 if not morph.giant_leaves else 0.3)
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
        for lx, ly in sample_leaf_polygon(
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
            pygame.draw.polygon(surface, morph.leaf_colour, lpts)
            edge = (
                max(0, morph.leaf_colour[0] - 20),
                max(0, morph.leaf_colour[1] - 15),
                max(0, morph.leaf_colour[2] - 15),
            )
            pygame.draw.polygon(surface, edge, lpts, 1)
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
                    pygame.draw.line(
                        surface,
                        vein,
                        (int(fx), int(fy)),
                        (int(fx + math.cos(ang + 1.15) * leaf_w * 0.35), int(fy + math.sin(ang + 1.15) * leaf_w * 0.35)),
                        1,
                    )

    # Flowers
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
            radius = max(10.0, morph.flower_radius * max_height * 0.13)
            if morph.glow:
                glow = pygame.Surface((int(radius * 5), int(radius * 5)), pygame.SRCALPHA)
                gcol = (
                    min(255, colour[0] + 30),
                    min(255, colour[1] + 50),
                    min(255, colour[2] + 70),
                    70,
                )
                pygame.draw.circle(
                    glow,
                    gcol,
                    (glow.get_width() // 2, glow.get_height() // 2),
                    int(radius * 1.8),
                )
                surface.blit(glow, (fx - glow.get_width() // 2, fy - glow.get_height() // 2))

            petal = sample_petal_polygon(
                radius=radius,
                petals=morph.petals,
                lobe_amp=0.28 + morph.petal_amp * 0.25,
                phase=morph.stem_phase * 0.2,
                steps_per_petal=10,
            )
            ppts = [(int(fx + x), int(fy + y)) for x, y in petal]
            if len(ppts) >= 3:
                pygame.draw.polygon(surface, colour, ppts)
                pygame.draw.polygon(
                    surface,
                    (max(0, colour[0] - 35), max(0, colour[1] - 35), max(0, colour[2] - 35)),
                    ppts,
                    1,
                )

            center_col = (36, 32, 28) if morph.eyes or morph.face else (245, 220, 95)
            pygame.draw.circle(surface, center_col, (fx, fy), max(3, int(radius * 0.28)))

            if morph.eyes:
                pygame.draw.circle(surface, (250, 250, 245), (fx - 4, fy - 1), 3)
                pygame.draw.circle(surface, (250, 250, 245), (fx + 4, fy - 1), 3)
                pygame.draw.circle(surface, (20, 20, 20), (fx - 4, fy - 1), 1)
                pygame.draw.circle(surface, (20, 20, 20), (fx + 4, fy - 1), 1)
            if morph.face:
                pygame.draw.circle(surface, (20, 20, 20), (fx - 4, fy - 2), 1)
                pygame.draw.circle(surface, (20, 20, 20), (fx + 4, fy - 2), 1)
                pygame.draw.arc(surface, (20, 20, 20), (fx - 6, fy - 1, 12, 8), 3.5, 5.9, 1)
            if morph.thunder and j == 0:
                pulse = 0.5 + 0.5 * math.sin(time_s * 4.5 + morph.stem_phase)
                pygame.draw.circle(surface, (235, 230, 120), (fx, fy), int(radius + 4 + pulse * 6), 1)


def render_plant_card(
    morph: MorphParams,
    size: Tuple[int, int] = (260, 320),
    time_s: float = 0.35,
) -> pygame.Surface:
    w, h = size
    surf = pygame.Surface((w, h))
    surf.fill(CARD)
    pygame.draw.ellipse(surf, (48, 72, 54), (24, h - 78, w - 48, 40))
    draw_morph_plant(surf, morph, (w // 2, h - 56), int(h * 0.58), time_s=time_s)

    font = pygame.font.SysFont("dejavusans", 16)
    small = pygame.font.SysFont("dejavusans", 12)
    surf.blit(font.render(morph.label, True, INK), (14, 12))
    y = 34
    line = ""
    for word in morph.note.split():
        trial = (line + " " + word).strip()
        if small.size(trial)[0] > w - 28:
            surf.blit(small.render(line, True, MUTED), (14, y))
            y += 15
            line = word
        else:
            line = trial
    if line:
        surf.blit(small.render(line, True, MUTED), (14, y))
    return surf


def render_gallery(
    morphs: Optional[List[MorphParams]] = None,
    cols: int = 4,
    card_size: Tuple[int, int] = (260, 320),
    time_s: float = 0.35,
) -> pygame.Surface:
    morphs = morphs or demo_catalog()
    cols = max(1, cols)
    rows = (len(morphs) + cols - 1) // cols
    pad = 16
    cw, ch = card_size
    width = pad + cols * (cw + pad)
    height = 72 + pad + rows * (ch + pad)
    gallery = pygame.Surface((width, height))
    gallery.fill(BG)

    pygame.font.init()
    title_font = pygame.font.SysFont("dejavusans", 28, bold=True)
    sub_font = pygame.font.SysFont("dejavusans", 14)
    gallery.blit(title_font.render("Sine Farm — morph preview", True, INK), (pad, 18))
    gallery.blit(
        sub_font.render(
            "Sine stems/branches · hybrid leaves/flowers · simple ornaments  |  not wired into the game yet",
            True,
            MUTED,
        ),
        (pad, 50),
    )

    for i, morph in enumerate(morphs):
        r, c = divmod(i, cols)
        card = render_plant_card(morph, size=card_size, time_s=time_s + i * 0.05)
        x = pad + c * (cw + pad)
        y = 72 + pad + r * (ch + pad)
        gallery.blit(card, (x, y))
    return gallery


def save_gallery(path: Path, **kwargs) -> Path:
    pygame.init()
    pygame.font.init()
    surf = render_gallery(**kwargs)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surf, str(path))
    return path

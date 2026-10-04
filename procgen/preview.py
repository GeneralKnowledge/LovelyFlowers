"""Gallery / card preview helpers for morph plants."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import pygame

from procgen.draw_pygame import draw_morph_plant
from procgen.morph import MorphParams, demo_catalog

BG = (24, 38, 32)
CARD = (36, 54, 46)
INK = (232, 238, 224)
MUTED = (168, 188, 172)


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
            "Sine stems/branches · hybrid leaves/flowers · simple ornaments",
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

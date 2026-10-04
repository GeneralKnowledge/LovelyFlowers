"""Sine Farm — Pygame front-end for the plant breeding greenhouse."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple

import pygame

from game.competitions import COMPETITIONS, TRIALS
from game.names import humorous_description
from game.state import SAVE_PATH, SEED_CATALOG, UPGRADES, GameState
from game.world import LOCATIONS, KIND_LABELS
from genetics.alleles import COLOUR_LOCUS, SHAPE_LOCUS
from genetics.mutations import MUTATION_CATALOG
from ui import theme
from ui.plant_renderer import draw_plant, plant_portrait
from procgen.audio import blip_from_morph, set_enabled
from procgen.morph import morph_from_phenotype, seed_from_plant_id


WIDTH, HEIGHT = 1180, 720
FPS = 60

COLOUR_LABELS = {a.id: a.label for a in COLOUR_LOCUS.alleles}
SHAPE_LABELS = {a.id: a.label for a in SHAPE_LOCUS.alleles}


class Button:
    def __init__(self, rect: pygame.Rect, label: str, action: str, enabled: bool = True):
        self.rect = rect
        self.label = label
        self.action = action
        self.enabled = enabled
        self.hover = False

    def draw(self, surf: pygame.Surface, font: pygame.font.Font) -> None:
        bg = theme.ACCENT if self.hover and self.enabled else theme.PANEL_INNER
        if not self.enabled:
            bg = (50, 60, 52)
        edge = theme.ACCENT if self.hover and self.enabled else theme.PANEL_EDGE
        pygame.draw.rect(surf, bg, self.rect, border_radius=6)
        pygame.draw.rect(surf, edge, self.rect, 1, border_radius=6)
        color = theme.TEXT if self.enabled else theme.TEXT_DIM
        text = font.render(self.label, True, color)
        surf.blit(text, text.get_rect(center=self.rect.center))


class LovelyFlowersApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Sine Farm — Serious Plant Breeding")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = self._load_font(18)
        self.font_sm = self._load_font(14)
        self.font_lg = self._load_font(28)
        self.font_xl = self._load_font(42)
        self.font_title = self._load_font(54)

        self.state = self._load_or_new()
        self.mode = "greenhouse"  # greenhouse, inspect, breed, contest, shop, collection, pedigree
        self.selected_id: Optional[str] = None
        self.breed_a: Optional[str] = None
        self.breed_b: Optional[str] = None
        self.buttons: List[Button] = []
        self.scroll = 0
        self.toast = ""
        self.toast_timer = 0.0
        self.time_s = 0.0
        self.show_help = False
        # Audio stays lazy/mute-safe (initialized on first blip)
        set_enabled(True)

    def _load_font(self, size: int) -> pygame.font.Font:
        # Prefer a slightly characterful system font
        for name in ("DejaVu Sans", "Liberation Sans", "FreeSans", "Arial"):
            path = pygame.font.match_font(name)
            if path:
                return pygame.font.Font(path, size)
        return pygame.font.SysFont("comicsansms", size)

    def _load_or_new(self) -> GameState:
        if SAVE_PATH.exists():
            try:
                return GameState.load(SAVE_PATH)
            except Exception:
                pass
        return GameState.new_game()

    def run(self) -> None:
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.time_s += dt
            if self.toast_timer > 0:
                self.toast_timer -= dt
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                elif event.type == pygame.KEYDOWN:
                    self._on_key(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._on_click(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self._on_hover(event.pos)
                elif event.type == pygame.MOUSEWHEEL:
                    self.scroll = max(0, self.scroll - event.y * 24)

            self._draw()
            pygame.display.flip()

    def _quit(self) -> None:
        try:
            self.state.save(SAVE_PATH)
        except Exception:
            pass
        pygame.quit()
        sys.exit(0)

    def _toast(self, msg: str) -> None:
        self.toast = msg
        self.toast_timer = 3.5

    def _on_key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            if self.show_help:
                self.show_help = False
            elif self.mode != "greenhouse":
                self.mode = "greenhouse"
            else:
                self._quit()
        elif event.key == pygame.K_SPACE:
            matured = self.state.advance_time(8)
            if matured:
                self._toast("Matured: " + ", ".join(matured[:3]))
                self._blip_named(matured[0], "mature")
            else:
                self._toast("Time passes in the greenhouse...")
            self.state.save(SAVE_PATH)
        elif event.key == pygame.K_s:
            self.state.save(SAVE_PATH)
            self._toast("Saved.")
        elif event.key == pygame.K_n and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.state = GameState.new_game()
            self.selected_id = None
            self._toast("New greenhouse started.")
        elif event.key == pygame.K_h:
            self.show_help = not self.show_help
        elif event.key == pygame.K_1:
            self.mode = "greenhouse"
        elif event.key == pygame.K_2:
            self.mode = "shop"
        elif event.key == pygame.K_3:
            self.mode = "breed"
        elif event.key == pygame.K_4:
            self.mode = "contest"
        elif event.key == pygame.K_5:
            self.mode = "travel"
        elif event.key == pygame.K_6:
            self.mode = "collection"

    def _on_hover(self, pos: Tuple[int, int]) -> None:
        for b in self.buttons:
            b.hover = b.rect.collidepoint(pos) and b.enabled

    def _on_click(self, pos: Tuple[int, int]) -> None:
        for b in self.buttons:
            if b.enabled and b.rect.collidepoint(pos):
                self._do_action(b.action)
                return
        # Pot clicks in greenhouse
        if self.mode == "greenhouse":
            for i, rect in enumerate(self._pot_rects()):
                if rect.collidepoint(pos):
                    pid = self.state.pot_assignments[i] if i < len(self.state.pot_assignments) else None
                    if pid:
                        self.selected_id = pid
                        self.mode = "inspect"
                    return

    def _do_action(self, action: str) -> None:
        if action == "goto:greenhouse":
            self.mode = "greenhouse"
        elif action == "goto:shop":
            self.mode = "shop"
        elif action == "goto:breed":
            self.mode = "breed"
            self.breed_a = self.selected_id
            self.breed_b = None
        elif action == "goto:contest":
            self.mode = "contest"
        elif action == "goto:collection":
            self.mode = "collection"
        elif action == "goto:travel":
            self.mode = "travel"
        elif action == "goto:lab":
            self.mode = "lab"
        elif action == "goto:trials":
            self.mode = "trials"
        elif action == "goto:pedigree":
            self.mode = "pedigree"
        elif action == "goto:inspect":
            self.mode = "inspect"
        elif action == "advance":
            matured = self.state.advance_time(8)
            self._toast("Matured: " + ", ".join(matured) if matured else "Growing...")
            if matured:
                self._blip_named(matured[0], "mature")
            self.state.save(SAVE_PATH)
        elif action == "save":
            self.state.save(SAVE_PATH)
            self._toast("Garden saved.")
        elif action == "help":
            self.show_help = not self.show_help
        elif action.startswith("buy_seed:"):
            quality = action.split(":", 1)[1]
            plant = self.state.buy_seed(quality)
            if plant:
                self.selected_id = plant.id
                self._toast(f"Planted {plant.name}")
                self.state.save(SAVE_PATH)
        elif action.startswith("buy_up:"):
            uid = action.split(":", 1)[1]
            if self.state.buy_upgrade(uid):
                self._toast("Upgrade purchased")
                self.state.save(SAVE_PATH)
        elif action == "sell":
            if self.selected_id:
                val = self.state.sell_plant(self.selected_id)
                if val is not None:
                    self._toast(f"Sold for ${val:.1f}")
                    self.selected_id = None
                    self.mode = "greenhouse"
                    self.state.save(SAVE_PATH)
        elif action == "favourite":
            if self.selected_id:
                self.state.toggle_favourite(self.selected_id)
        elif action.startswith("select:"):
            self.selected_id = action.split(":", 1)[1]
            self.mode = "inspect"
        elif action.startswith("breed_pick:"):
            pid = action.split(":", 1)[1]
            if not self.breed_a:
                self.breed_a = pid
            elif not self.breed_b and pid != self.breed_a:
                self.breed_b = pid
            else:
                self.breed_a = pid
                self.breed_b = None
        elif action == "breed_clear":
            self.breed_a = None
            self.breed_b = None
        elif action == "breed_go":
            if self.breed_a and self.breed_b:
                kids = self.state.breed_plants(self.breed_a, self.breed_b)
                if kids:
                    self._toast(f"Litter of {len(kids)}: " + ", ".join(k.name for k in kids))
                    self.selected_id = kids[0].id
                    self.mode = "greenhouse"
                    self._blip_plant(kids[0], "breed")
                    self.state.save(SAVE_PATH)
                else:
                    self._toast(self.state.messages[-1] if self.state.messages else "Breeding failed")
        elif action == "breed_rad":
            if self.breed_a and self.breed_b:
                kids = self.state.breed_plants(self.breed_a, self.breed_b, under_radiation=True)
                if kids:
                    self._toast("Irradiated litter: " + ", ".join(k.name for k in kids))
                    self.selected_id = kids[0].id
                    self.mode = "greenhouse"
                    self._blip_plant(kids[0], "breed")
                    self.state.save(SAVE_PATH)
                else:
                    self._toast(self.state.messages[-1] if self.state.messages else "Radiation cross failed")
        elif action.startswith("contest_enter:"):
            comp_id = action.split(":", 1)[1]
            if self.selected_id:
                result = self.state.enter_competition(comp_id, self.selected_id)
                if result:
                    self._toast(f"{result.ribbon}: place {result.place}")
                    self.state.save(SAVE_PATH)
        elif action.startswith("explore:"):
            loc_id = action.split(":", 1)[1]
            wild = self.state.explore(loc_id)
            if wild:
                self.selected_id = wild.id
                self._toast(f"Found {wild.name} ({KIND_LABELS.get(wild.species_kind, wild.species_kind)})")
                self.mode = "inspect"
                self.state.save(SAVE_PATH)
            else:
                self._toast(self.state.messages[-1] if self.state.messages else "Expedition failed")
        elif action.startswith("irradiate:"):
            intensity = action.split(":", 1)[1]
            if self.selected_id:
                report = self.state.irradiate_plant(self.selected_id, intensity=intensity)
                if report:
                    if not report.get("survived", True):
                        self._toast("Specimen destroyed by radiation.")
                        self.selected_id = None
                        self.mode = "greenhouse"
                    else:
                        gained = report.get("mutations_gained") or []
                        self._toast(
                            f"Radiation done. +{len(gained)} mutation allele(s)."
                            if gained
                            else "Radiation done. Subtle chaos."
                        )
                    self.state.save(SAVE_PATH)
        elif action.startswith("trial:"):
            trial_id = action.split(":", 1)[1]
            if self.selected_id:
                result = self.state.run_plant_trial(trial_id, self.selected_id)
                if result:
                    self._toast(f"Trial {result.grade}: {result.advice[:60]}")
                    self.state.save(SAVE_PATH)

    # --- drawing -------------------------------------------------------
    def _draw(self) -> None:
        self._draw_background()
        self.buttons = []
        self._draw_header()
        if self.mode == "greenhouse":
            self._draw_greenhouse()
        elif self.mode == "inspect":
            self._draw_inspect()
        elif self.mode == "breed":
            self._draw_breed()
        elif self.mode == "contest":
            self._draw_contest()
        elif self.mode == "shop":
            self._draw_shop()
        elif self.mode == "collection":
            self._draw_collection()
        elif self.mode == "pedigree":
            self._draw_pedigree()
        elif self.mode == "travel":
            self._draw_travel()
        elif self.mode == "lab":
            self._draw_lab()
        elif self.mode == "trials":
            self._draw_trials()
        self._draw_nav()
        if self.mode == "greenhouse":
            self._draw_log()
        if self.toast_timer > 0:
            self._draw_toast()
        if self.show_help:
            self._draw_help()

    def _draw_background(self) -> None:
        # Vertical gradient + subtle leaf lattice
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(theme.BG_TOP[0] * (1 - t) + theme.BG_BOTTOM[0] * t)
            g = int(theme.BG_TOP[1] * (1 - t) + theme.BG_BOTTOM[1] * t)
            b = int(theme.BG_TOP[2] * (1 - t) + theme.BG_BOTTOM[2] * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIDTH, y))
        # soft vignette bars (glasshouse mullions)
        for x in range(80, WIDTH, 160):
            pygame.draw.line(self.screen, (40, 65, 50), (x, 70), (x, HEIGHT), 1)

    def _draw_header(self) -> None:
        title = self.font_lg.render("Sine Farm", True, theme.ACCENT)
        self.screen.blit(title, (24, 14))
        sub = self.font_sm.render(
            "Collect · Breed · Genetically improve · Compete · Sell · Repeat",
            True,
            theme.TEXT_DIM,
        )
        self.screen.blit(sub, (24, 46))
        stats = self.font.render(
            f"Day {self.state.day:.1f}   ${self.state.money:.1f}   Prestige {self.state.prestige}   "
            f"Pots {sum(1 for p in self.state.pot_assignments if p)}/{self.state.greenhouse_slots}",
            True,
            theme.TEXT,
        )
        self.screen.blit(stats, (WIDTH - stats.get_width() - 24, 22))

    def _draw_nav(self) -> None:
        labels = [
            ("Greenhouse", "goto:greenhouse", self.mode == "greenhouse"),
            ("Shop", "goto:shop", self.mode == "shop"),
            ("Breed", "goto:breed", self.mode == "breed"),
            ("Compete", "goto:contest", self.mode in ("contest", "trials")),
            ("Travel", "goto:travel", self.mode == "travel"),
            ("Lab", "goto:lab", self.mode == "lab"),
            ("Catalog", "goto:collection", self.mode == "collection"),
            ("Wait", "advance", False),
            ("Save", "save", False),
            ("?", "help", False),
        ]
        x = 10
        y = HEIGHT - 48
        for label, action, active in labels:
            w = 88 if len(label) <= 4 else (100 if len(label) < 9 else 110)
            rect = pygame.Rect(x, y, w, 32)
            b = Button(rect, label, action)
            if active:
                b.hover = True
            self.buttons.append(b)
            b.draw(self.screen, self.font_sm)
            x += rect.width + 5

    def _pot_rects(self) -> List[pygame.Rect]:
        slots = self.state.greenhouse_slots
        cols = min(6, max(3, slots))
        rows = (slots + cols - 1) // cols
        area = pygame.Rect(40, 90, WIDTH - 360, HEIGHT - 200)
        rects = []
        cell_w = area.width // cols
        cell_h = area.height // max(1, rows)
        for i in range(slots):
            c, r = i % cols, i // cols
            cx = area.x + c * cell_w + cell_w // 2
            cy = area.y + r * cell_h + cell_h // 2 + 20
            rects.append(pygame.Rect(cx - 55, cy - 90, 110, 140))
        return rects

    def _draw_greenhouse(self) -> None:
        brand = self.font_xl.render("Greenhouse", True, theme.TEXT)
        self.screen.blit(brand, (40, 78))
        hint = self.font_sm.render(
            "Click a plant to inspect. Space waits. Breed exceptional bloodlines.",
            True,
            theme.TEXT_DIM,
        )
        self.screen.blit(hint, (40, 118))

        rects = self._pot_rects()
        mouse = pygame.mouse.get_pos()
        for i, rect in enumerate(rects):
            hover = rect.collidepoint(mouse)
            pygame.draw.rect(
                self.screen,
                theme.POT_HOVER if hover else theme.POT_SLOT,
                rect,
                border_radius=10,
            )
            pygame.draw.rect(self.screen, theme.PANEL_EDGE, rect, 1, border_radius=10)
            pid = self.state.pot_assignments[i] if i < len(self.state.pot_assignments) else None
            label = self.font_sm.render(f"Pot {i+1}", True, theme.TEXT_DIM)
            self.screen.blit(label, (rect.x + 8, rect.bottom - 20))
            if pid and pid in self.state.plants:
                plant = self.state.plants[pid]
                draw_plant(
                    self.screen,
                    plant,
                    (rect.centerx, rect.bottom - 36),
                    90,
                    time_s=self.time_s,
                )
                name = self.font_sm.render(plant.name[:14], True, theme.TEXT)
                self.screen.blit(name, name.get_rect(midtop=(rect.centerx, rect.y + 6)))
                if not plant.mature:
                    # growth bar
                    bar = pygame.Rect(rect.x + 12, rect.y + 24, rect.width - 24, 6)
                    pygame.draw.rect(self.screen, (30, 40, 32), bar, border_radius=3)
                    fill = bar.copy()
                    fill.width = int(bar.width * plant.growth_progress)
                    pygame.draw.rect(self.screen, theme.GOOD, fill, border_radius=3)
                elif plant.favourite:
                    star = self.font_sm.render("★", True, theme.GOLD)
                    self.screen.blit(star, (rect.right - 18, rect.y + 6))
            else:
                empty = self.font_sm.render("Empty", True, theme.TEXT_DIM)
                self.screen.blit(empty, empty.get_rect(center=rect.center))

    def _panel(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, theme.PANEL, rect, border_radius=12)
        pygame.draw.rect(self.screen, theme.PANEL_EDGE, rect, 1, border_radius=12)

    def _draw_inspect(self) -> None:
        plant = self.state.plants.get(self.selected_id) if self.selected_id else None
        if not plant or plant.sold:
            self.mode = "greenhouse"
            return
        ph = plant.phenotype()
        left = pygame.Rect(40, 90, 360, HEIGHT - 200)
        right = pygame.Rect(420, 90, WIDTH - 460, HEIGHT - 200)
        self._panel(left)
        self._panel(right)

        portrait = plant_portrait(plant, 220, self.time_s)
        self.screen.blit(portrait, portrait.get_rect(center=(left.centerx, left.y + 140)))
        name = self.font_lg.render(plant.name, True, theme.ACCENT)
        self.screen.blit(name, name.get_rect(midtop=(left.centerx, left.y + 270)))
        meta = self.font_sm.render(
            f"{KIND_LABELS.get(plant.species_kind, plant.species_kind)}  ·  "
            f"Gen {plant.generation}  ·  Age {plant.age_days:.1f}d  ·  "
            f"{'Mature' if plant.mature else 'Growing'}"
            + ("  ·  Wild" if plant.wild else "")
            + ("  ·  Irradiated" if plant.irradiated else ""),
            True,
            theme.TEXT_DIM,
        )
        self.screen.blit(meta, meta.get_rect(midtop=(left.centerx, left.y + 308)))
        desc = humorous_description(plant)
        self._blit_wrapped(desc, self.font_sm, theme.TEXT, left.inflate(-30, -20).move(0, 250), 300)

        actions = [
            ("Favourite" if not plant.favourite else "Unfavourite", "favourite"),
            ("Pedigree", "goto:pedigree"),
            ("Breed", "goto:breed"),
            ("Trial", "goto:trials"),
            ("Lab", "goto:lab"),
            ("Compete", "goto:contest"),
            ("Sell $%.1f" % (ph.value if plant.mature else ph.value * 0.35), "sell"),
            ("Back", "goto:greenhouse"),
        ]
        for i, (label, action) in enumerate(actions):
            col, row = i % 2, i // 2
            rect = pygame.Rect(left.x + 24 + col * 160, left.bottom - 130 + row * 30, 150, 26)
            enabled = plant.mature or action in (
                "favourite",
                "goto:greenhouse",
                "sell",
                "goto:pedigree",
                "goto:lab",
            )
            b = Button(rect, label, action, enabled=enabled)
            self.buttons.append(b)
            b.draw(self.screen, self.font_sm)

        # Right: traits
        y = right.y + 20
        header = self.font_lg.render("Specimen Sheet", True, theme.TEXT)
        self.screen.blit(header, (right.x + 24, y))
        y += 40
        stats = [
            ("Height", ph.height),
            ("Width", ph.width),
            ("Growth", ph.growth),
            ("Yield", ph.yield_),
            ("Flower", ph.flower),
            ("Leaf", ph.leaf),
            ("Branch", ph.branch),
            ("Stem", ph.stem),
            ("Water", ph.water),
            ("Disease Res.", ph.disease),
            ("Quality", ph.quality),
            ("Stability", ph.stability),
            ("Symmetry", ph.symmetry),
            ("Beauty", ph.beauty),
            ("Size Score", ph.size_score),
            ("Speed Score", ph.speed_score),
            ("Strangeness", ph.strangeness),
        ]
        for i, (label, val) in enumerate(stats):
            col = 0 if i < 9 else 1
            row = i if i < 9 else i - 9
            x = right.x + 24 + col * 340
            yy = y + row * 26
            self.screen.blit(self.font_sm.render(label, True, theme.TEXT_DIM), (x, yy))
            bar = pygame.Rect(x + 110, yy + 4, 160, 10)
            pygame.draw.rect(self.screen, (30, 40, 32), bar, border_radius=3)
            fill = bar.copy()
            fill.width = int(bar.width * max(0, min(1.0, val)))
            color = theme.ACCENT if val > 0.75 else theme.GOOD
            pygame.draw.rect(self.screen, color, fill, border_radius=3)

        y = right.y + 300
        info = [
            f"Colour: {COLOUR_LABELS.get(ph.colour_id, ph.colour_id)}",
            f"Shape: {SHAPE_LABELS.get(ph.shape_id, ph.shape_id)}",
            f"Maturity time: {ph.maturity_days:.1f} days",
            f"Market value: ${ph.value:.1f}",
        ]
        for line in info:
            self.screen.blit(self.font.render(line, True, theme.TEXT), (right.x + 24, y))
            y += 26

        y += 8
        self.screen.blit(self.font.render("Genetics", True, theme.ACCENT), (right.x + 24, y))
        y += 28
        if ph.expressed_mutations:
            for mid in ph.expressed_mutations:
                label = self.state.collection.mutation_display(mid)
                self.screen.blit(
                    self.font_sm.render(f"• Expressed: {label}", True, theme.GOLD),
                    (right.x + 24, y),
                )
                y += 20
        else:
            self.screen.blit(
                self.font_sm.render("• No expressed mutations", True, theme.TEXT_DIM),
                (right.x + 24, y),
            )
            y += 20
        for mid in ph.carrier_mutations:
            label = self.state.collection.mutation_display(mid)
            self.screen.blit(
                self.font_sm.render(f"• Hidden carrier: {label}", True, theme.TEXT_DIM),
                (right.x + 24, y),
            )
            y += 20

        if plant.competition_history:
            y += 8
            self.screen.blit(self.font.render("Competition History", True, theme.ACCENT), (right.x + 24, y))
            y += 24
            for c in plant.competition_history[-4:]:
                self.screen.blit(
                    self.font_sm.render(
                        f"{c['competition_name']}: {c['ribbon']} (#{c['place']})",
                        True,
                        theme.TEXT,
                    ),
                    (right.x + 24, y),
                )
                y += 18

        if plant.trial_history:
            y += 8
            self.screen.blit(self.font.render("Trial Cards", True, theme.ACCENT), (right.x + 24, y))
            y += 24
            last = plant.trial_history[-1]
            grades = last.get("category_scores", {})
            grade_line = "  ".join(f"{k[:3]}:{v}" for k, v in grades.items())
            self.screen.blit(
                self.font_sm.render(
                    f"{last.get('trial_name')}: {last.get('grade')} — {grade_line}",
                    True,
                    theme.TEXT,
                ),
                (right.x + 24, y),
            )

    def _draw_breed(self) -> None:
        panel = pygame.Rect(40, 90, WIDTH - 80, HEIGHT - 200)
        self._panel(panel)
        self.screen.blit(self.font_lg.render("Cross-Pollination Bench", True, theme.ACCENT), (panel.x + 24, panel.y + 16))
        self.screen.blit(
            self.font_sm.render(
                "Pick two mature parents. Offspring inherit alleles — not averages.",
                True,
                theme.TEXT_DIM,
            ),
            (panel.x + 24, panel.y + 52),
        )

        # Parent slots
        for i, (label, pid) in enumerate([("Parent A", self.breed_a), ("Parent B", self.breed_b)]):
            rect = pygame.Rect(panel.x + 40 + i * 260, panel.y + 90, 220, 180)
            pygame.draw.rect(self.screen, theme.PANEL_INNER, rect, border_radius=8)
            pygame.draw.rect(self.screen, theme.ACCENT if pid else theme.PANEL_EDGE, rect, 1, border_radius=8)
            self.screen.blit(self.font.render(label, True, theme.TEXT_DIM), (rect.x + 12, rect.y + 8))
            if pid and pid in self.state.plants:
                p = self.state.plants[pid]
                draw_plant(self.screen, p, (rect.centerx, rect.bottom - 30), 100, self.time_s)
                self.screen.blit(
                    self.font_sm.render(f"{p.name}  Gen {p.generation}", True, theme.TEXT),
                    (rect.x + 12, rect.y + 36),
                )

        ok, msg = (False, "Select two parents")
        if self.breed_a and self.breed_b:
            ok, msg = self.state.can_breed(self.breed_a, self.breed_b)
        self.screen.blit(self.font_sm.render(msg, True, theme.GOOD if ok else theme.TEXT_DIM), (panel.x + 40, panel.y + 290))

        b = Button(pygame.Rect(panel.x + 40, panel.y + 320, 140, 34), "Breed", "breed_go", enabled=ok)
        self.buttons.append(b)
        b.draw(self.screen, self.font)
        rad_ok = ok and self.state.has_radiation_access()
        b_rad = Button(
            pygame.Rect(panel.x + 190, panel.y + 320, 180, 34),
            "Irradiated Cross",
            "breed_rad",
            enabled=rad_ok,
        )
        self.buttons.append(b_rad)
        b_rad.draw(self.screen, self.font)
        b2 = Button(pygame.Rect(panel.x + 380, panel.y + 320, 100, 34), "Clear", "breed_clear")
        self.buttons.append(b2)
        b2.draw(self.screen, self.font)
        b3 = Button(pygame.Rect(panel.x + 490, panel.y + 320, 100, 34), "Back", "goto:greenhouse")
        self.buttons.append(b3)
        b3.draw(self.screen, self.font)
        if not self.state.has_radiation_access():
            self.screen.blit(
                self.font_sm.render("Irradiated crosses unlock via Abandoned Lab or chamber kit.", True, theme.TEXT_DIM),
                (panel.x + 40, panel.y + 360),
            )

        # Mature plant picker
        self.screen.blit(self.font.render("Mature plants", True, theme.TEXT), (panel.x + 560, panel.y + 90))
        mature = [p for p in self.state.living_plants() if p.mature]
        y = panel.y + 120
        for p in mature[:12]:
            rect = pygame.Rect(panel.x + 560, y, 480, 28)
            selected = p.id in (self.breed_a, self.breed_b)
            pygame.draw.rect(
                self.screen,
                theme.ACCENT_DIM if selected else theme.PANEL_INNER,
                rect,
                border_radius=4,
            )
            label = (
                f"{p.name}  [{KIND_LABELS.get(p.species_kind, '?')[:6]}]  "
                f"Gen{p.generation}  mut:{len(p.phenotype().expressed_mutations)}  ${p.value:.0f}"
            )
            self.screen.blit(self.font_sm.render(label, True, theme.TEXT), (rect.x + 8, rect.y + 6))
            btn = Button(rect, "", f"breed_pick:{p.id}")
            self.buttons.append(btn)
            y += 32

    def _draw_contest(self) -> None:
        panel = pygame.Rect(40, 90, WIDTH - 80, HEIGHT - 200)
        self._panel(panel)
        self.screen.blit(self.font_lg.render("Competitions", True, theme.ACCENT), (panel.x + 24, panel.y + 16))
        self.screen.blit(
            self.font_sm.render(
                "No complex markets — just enter a plant, get a placing, collect ribbons.",
                True,
                theme.TEXT_DIM,
            ),
            (panel.x + 24, panel.y + 52),
        )

        plant = self.state.plants.get(self.selected_id) if self.selected_id else None
        if plant and not plant.sold:
            self.screen.blit(
                self.font.render(f"Selected: {plant.name} (Gen {plant.generation})", True, theme.TEXT),
                (panel.x + 24, panel.y + 80),
            )
            draw_plant(self.screen, plant, (panel.x + 980, panel.y + 200), 140, self.time_s)
        else:
            self.screen.blit(
                self.font.render("Select a mature plant from the greenhouse first.", True, theme.DANGER),
                (panel.x + 24, panel.y + 80),
            )

        y = panel.y + 120
        for comp in COMPETITIONS:
            locked = self.state.prestige < comp.prestige_required
            rect = pygame.Rect(panel.x + 24, y, 700, 70)
            pygame.draw.rect(self.screen, theme.PANEL_INNER, rect, border_radius=8)
            pygame.draw.rect(
                self.screen,
                theme.PANEL_EDGE if locked else theme.ACCENT,
                rect,
                1,
                border_radius=8,
            )
            title = f"{comp.name}" + ("  [LOCKED]" if locked else "")
            self.screen.blit(self.font.render(title, True, theme.TEXT_DIM if locked else theme.TEXT), (rect.x + 14, rect.y + 10))
            self.screen.blit(self.font_sm.render(comp.tagline, True, theme.TEXT_DIM), (rect.x + 14, rect.y + 36))
            fee = self.font_sm.render(
                f"Fee ${comp.entry_fee}  ·  Need prestige {comp.prestige_required}  ·  Purse ${comp.purse[0]}",
                True,
                theme.TEXT_DIM,
            )
            self.screen.blit(fee, (rect.x + 360, rect.y + 12))
            can = (
                plant is not None
                and plant.mature
                and not locked
                and self.state.money >= comp.entry_fee
            )
            b = Button(
                pygame.Rect(rect.right - 130, rect.y + 18, 110, 34),
                "Enter",
                f"contest_enter:{comp.id}",
                enabled=can,
            )
            self.buttons.append(b)
            b.draw(self.screen, self.font_sm)
            y += 80

        if self.state.last_contest:
            lc = self.state.last_contest
            box = pygame.Rect(panel.x + 760, panel.y + 320, 300, 120)
            pygame.draw.rect(self.screen, theme.PANEL_INNER, box, border_radius=8)
            self.screen.blit(self.font.render("Last Result", True, theme.GOLD), (box.x + 12, box.y + 10))
            self._blit_wrapped(
                f"{lc['ribbon']} — {lc['summary']} (+${lc['prize']})",
                self.font_sm,
                theme.TEXT,
                box.inflate(-20, -40).move(0, 20),
                280,
            )

        b = Button(pygame.Rect(panel.x + 24, panel.bottom - 50, 120, 32), "Back", "goto:greenhouse")
        self.buttons.append(b)
        b.draw(self.screen, self.font_sm)
        bt = Button(pygame.Rect(panel.x + 160, panel.bottom - 50, 160, 32), "Trial Shows", "goto:trials")
        self.buttons.append(bt)
        bt.draw(self.screen, self.font_sm)

    def _draw_shop(self) -> None:
        panel = pygame.Rect(40, 90, WIDTH - 80, HEIGHT - 200)
        self._panel(panel)
        self.screen.blit(self.font_lg.render("Seed Counter & Improvements", True, theme.ACCENT), (panel.x + 24, panel.y + 16))
        self.screen.blit(
            self.font_sm.render("Money is simple. Seeds in, extraordinary plants out.", True, theme.TEXT_DIM),
            (panel.x + 24, panel.y + 52),
        )

        y = panel.y + 100
        self.screen.blit(self.font.render("Seeds", True, theme.TEXT), (panel.x + 24, y))
        y += 36
        for seed in SEED_CATALOG:
            rect = pygame.Rect(panel.x + 24, y, 500, 56)
            pygame.draw.rect(self.screen, theme.PANEL_INNER, rect, border_radius=8)
            self.screen.blit(self.font.render(seed["name"], True, theme.TEXT), (rect.x + 14, rect.y + 8))
            self.screen.blit(
                self.font_sm.render(f"${seed['cost']}  ·  {seed['quality']} genetics", True, theme.TEXT_DIM),
                (rect.x + 14, rect.y + 30),
            )
            b = Button(
                pygame.Rect(rect.right - 120, rect.y + 12, 100, 32),
                "Buy",
                f"buy_seed:{seed['id']}",
                enabled=self.state.money >= seed["cost"],
            )
            self.buttons.append(b)
            b.draw(self.screen, self.font_sm)
            y += 66

        y = panel.y + 100
        self.screen.blit(self.font.render("Greenhouse Upgrades", True, theme.TEXT), (panel.x + 580, y))
        y += 36
        for up in UPGRADES:
            owned = up["id"] in self.state.owned_upgrades
            rect = pygame.Rect(panel.x + 580, y, 500, 56)
            pygame.draw.rect(self.screen, theme.PANEL_INNER, rect, border_radius=8)
            self.screen.blit(
                self.font.render(up["name"] + (" (owned)" if owned else ""), True, theme.TEXT),
                (rect.x + 14, rect.y + 8),
            )
            self.screen.blit(
                self.font_sm.render(f"${up['cost']}  ·  {up['desc']}", True, theme.TEXT_DIM),
                (rect.x + 14, rect.y + 30),
            )
            b = Button(
                pygame.Rect(rect.right - 120, rect.y + 12, 100, 32),
                "Owned" if owned else "Buy",
                f"buy_up:{up['id']}",
                enabled=not owned and self.state.money >= up["cost"],
            )
            self.buttons.append(b)
            b.draw(self.screen, self.font_sm)
            y += 66

        b = Button(pygame.Rect(panel.x + 24, panel.bottom - 50, 120, 32), "Back", "goto:greenhouse")
        self.buttons.append(b)
        b.draw(self.screen, self.font_sm)

    def _draw_collection(self) -> None:
        panel = pygame.Rect(40, 90, WIDTH - 80, HEIGHT - 200)
        self._panel(panel)
        self.screen.blit(self.font_lg.render("Discovery Catalog", True, theme.ACCENT), (panel.x + 24, panel.y + 16))
        col = self.state.collection
        summary = (
            f"Mutations {len(col.mutations)}/{len(MUTATION_CATALOG)}  ·  "
            f"Colours {len(col.colours)}  ·  Shapes {len(col.shapes)}  ·  "
            f"Bloodlines {len(col.bloodlines)}  ·  Max Gen {col.max_generation}"
        )
        self.screen.blit(self.font_sm.render(summary, True, theme.TEXT_DIM), (panel.x + 24, panel.y + 52))

        y = panel.y + 90 - self.scroll
        self.screen.blit(self.font.render("Mutations", True, theme.TEXT), (panel.x + 24, max(panel.y + 80, y)))
        y += 30
        for entry in col.catalog_entries():
            if y > panel.bottom - 80:
                break
            if y > panel.y + 70:
                name_c = theme.GOLD if entry["known"] else theme.TEXT_DIM
                self.screen.blit(
                    self.font_sm.render(
                        f"{entry['name']}  [{entry['rarity']}]  — {entry['description']}",
                        True,
                        name_c,
                    ),
                    (panel.x + 36, y),
                )
            y += 22

        y += 16
        if y > panel.y + 70:
            self.screen.blit(self.font.render("Bloodlines", True, theme.TEXT), (panel.x + 24, y))
        y += 28
        for bl in sorted(col.bloodlines) or ["(Breed into generation 3+ to record a bloodline)"]:
            if y > panel.bottom - 80:
                break
            if y > panel.y + 70:
                self.screen.blit(self.font_sm.render(f"• {bl}", True, theme.TEXT), (panel.x + 36, y))
            y += 20

        y += 16
        if y > panel.y + 70:
            self.screen.blit(self.font.render("Ribbon Cabinet", True, theme.TEXT), (panel.x + 24, y))
        y += 28
        for w in col.winners[-8:]:
            if y > panel.bottom - 60:
                break
            if y > panel.y + 70:
                self.screen.blit(
                    self.font_sm.render(
                        f"{w.get('ribbon', '?')} — {w.get('plant_name')} @ {w.get('competition_name')}",
                        True,
                        theme.TEXT,
                    ),
                    (panel.x + 36, y),
                )
            y += 20

        b = Button(pygame.Rect(panel.x + 24, panel.bottom - 50, 120, 32), "Back", "goto:greenhouse")
        self.buttons.append(b)
        b.draw(self.screen, self.font_sm)

    def _draw_pedigree(self) -> None:
        panel = pygame.Rect(40, 90, WIDTH - 80, HEIGHT - 200)
        self._panel(panel)
        plant = self.state.plants.get(self.selected_id) if self.selected_id else None
        if not plant:
            self.mode = "greenhouse"
            return
        self.screen.blit(
            self.font_lg.render(f"Pedigree — {plant.name}", True, theme.ACCENT),
            (panel.x + 24, panel.y + 16),
        )
        tree = self.state.pedigree_tree(plant.id, depth=3)
        self._draw_pedigree_node(tree, panel.x + panel.width // 2, panel.y + 100, panel.width // 3)

        b = Button(pygame.Rect(panel.x + 24, panel.bottom - 50, 120, 32), "Back", "goto:inspect")
        self.buttons.append(b)
        b.draw(self.screen, self.font_sm)

    def _draw_pedigree_node(self, node: Dict, x: int, y: int, spread: float, depth: int = 0) -> None:
        if not node:
            return
        rect = pygame.Rect(0, 0, 160, 54)
        rect.center = (x, y)
        pygame.draw.rect(self.screen, theme.PANEL_INNER, rect, border_radius=6)
        pygame.draw.rect(self.screen, theme.ACCENT if depth == 0 else theme.PANEL_EDGE, rect, 1, border_radius=6)
        name = str(node.get("name", "?"))[:16]
        self.screen.blit(self.font_sm.render(name, True, theme.TEXT), (rect.x + 8, rect.y + 6))
        gen = node.get("generation", "?")
        muts = ", ".join(node.get("mutations", [])[:2]) or "—"
        self.screen.blit(
            self.font_sm.render(f"Gen {gen}  {muts}", True, theme.TEXT_DIM),
            (rect.x + 8, rect.y + 28),
        )
        parents = node.get("parents", [])
        if not parents:
            return
        n = len(parents)
        for i, parent in enumerate(parents):
            px = int(x - spread / 2 + (spread * i / max(1, n - 1) if n > 1 else 0))
            py = y + 95
            pygame.draw.line(self.screen, theme.PANEL_EDGE, (x, y + 27), (px, py - 27), 1)
            self._draw_pedigree_node(parent, px, py, spread / 2.2, depth + 1)

    def _draw_log(self) -> None:
        box = pygame.Rect(WIDTH - 320, 90, 290, 200)
        self._panel(box)
        self.screen.blit(self.font_sm.render("Greenhouse Log", True, theme.ACCENT), (box.x + 12, box.y + 8))
        y = box.y + 32
        for line in self.state.messages[-6:]:
            # Single-line clipped entries keep the log readable
            text = line if self.font_sm.size(line)[0] <= 266 else line[:42] + "…"
            self.screen.blit(self.font_sm.render(text, True, theme.TEXT), (box.x + 12, y))
            y += 22
            if y > box.bottom - 16:
                break

    def _draw_toast(self) -> None:
        text = self.font.render(self.toast, True, theme.TEXT)
        rect = text.get_rect(center=(WIDTH // 2, 70))
        bg = rect.inflate(28, 16)
        pygame.draw.rect(self.screen, theme.ACCENT_DIM, bg, border_radius=8)
        self.screen.blit(text, rect)

    def prestige_lock(self, loc) -> bool:
        return self.state.prestige < loc.prestige_required

    def _draw_trials(self) -> None:
        panel = pygame.Rect(40, 90, WIDTH - 80, HEIGHT - 200)
        self._panel(panel)
        self.screen.blit(self.font_lg.render("Trial Shows", True, theme.ACCENT), (panel.x + 24, panel.y + 16))
        self.screen.blit(
            self.font_sm.render(
                "Cheap keep-vs-sell evaluations — the test-race equivalent. Grades, not glory.",
                True,
                theme.TEXT_DIM,
            ),
            (panel.x + 24, panel.y + 52),
        )
        plant = self.state.plants.get(self.selected_id) if self.selected_id else None
        if plant and not plant.sold:
            self.screen.blit(
                self.font.render(
                    f"Selected: {plant.name} ({KIND_LABELS.get(plant.species_kind, '?')})",
                    True,
                    theme.TEXT,
                ),
                (panel.x + 24, panel.y + 80),
            )
        else:
            self.screen.blit(
                self.font.render("Select a mature specimen first.", True, theme.DANGER),
                (panel.x + 24, panel.y + 80),
            )

        y = panel.y + 120
        for trial in TRIALS:
            rect = pygame.Rect(panel.x + 24, y, 700, 56)
            pygame.draw.rect(self.screen, theme.PANEL_INNER, rect, border_radius=8)
            pygame.draw.rect(self.screen, theme.PANEL_EDGE, rect, 1, border_radius=8)
            self.screen.blit(self.font.render(trial.name, True, theme.TEXT), (rect.x + 14, rect.y + 8))
            self.screen.blit(self.font_sm.render(trial.tagline, True, theme.TEXT_DIM), (rect.x + 14, rect.y + 30))
            can = plant is not None and plant.mature and self.state.money >= trial.fee
            b = Button(
                pygame.Rect(rect.right - 130, rect.y + 12, 110, 32),
                f"${trial.fee}",
                f"trial:{trial.id}",
                enabled=can,
            )
            self.buttons.append(b)
            b.draw(self.screen, self.font_sm)
            y += 64

        if self.state.last_trial:
            lt = self.state.last_trial
            box = pygame.Rect(panel.x + 760, panel.y + 120, 300, 200)
            pygame.draw.rect(self.screen, theme.PANEL_INNER, box, border_radius=8)
            self.screen.blit(
                self.font.render(f"Grade {lt.get('grade')}", True, theme.GOLD),
                (box.x + 12, box.y + 10),
            )
            grades = lt.get("category_scores", {})
            yy = box.y + 44
            for cat, g in grades.items():
                self.screen.blit(self.font_sm.render(f"{cat}: {g}", True, theme.TEXT), (box.x + 12, yy))
                yy += 20
            self._blit_wrapped(
                lt.get("advice", ""),
                self.font_sm,
                theme.TEXT_DIM,
                box.inflate(-20, -120).move(0, 80),
                280,
            )

        b = Button(pygame.Rect(panel.x + 24, panel.bottom - 50, 120, 32), "Back", "goto:contest")
        self.buttons.append(b)
        b.draw(self.screen, self.font_sm)

    def _draw_travel(self) -> None:
        panel = pygame.Rect(40, 90, WIDTH - 80, HEIGHT - 200)
        self._panel(panel)
        self.screen.blit(self.font_lg.render("Expeditions", True, theme.ACCENT), (panel.x + 24, panel.y + 16))
        self.screen.blit(
            self.font_sm.render(
                "Travel is simulated for now — pay the fare, skip the walking, drag home weirdness. Real maps later.",
                True,
                theme.TEXT_DIM,
            ),
            (panel.x + 24, panel.y + 52),
        )
        self.screen.blit(
            self.font_sm.render(
                f"Current: {self.state.current_location}  ·  "
                f"Visited: {len(self.state.visited_locations)}/{len(LOCATIONS)}",
                True,
                theme.TEXT,
            ),
            (panel.x + 24, panel.y + 78),
        )

        y = panel.y + 110
        for loc in LOCATIONS:
            if loc.id == "home":
                continue
            locked = self.prestige_lock(loc)
            rect = pygame.Rect(panel.x + 24, y, WIDTH - 140, 62)
            pygame.draw.rect(self.screen, theme.PANEL_INNER, rect, border_radius=8)
            edge = theme.PANEL_EDGE if locked else (
                theme.DANGER if loc.special == "radiation_zone" else theme.ACCENT
            )
            pygame.draw.rect(self.screen, edge, rect, 1, border_radius=8)
            title = loc.name + ("  [LOCKED]" if locked else "")
            self.screen.blit(
                self.font.render(title, True, theme.TEXT_DIM if locked else theme.TEXT),
                (rect.x + 14, rect.y + 8),
            )
            kinds = ", ".join(sorted({KIND_LABELS.get(k, k) for k in loc.wild_kinds}))
            self.screen.blit(
                self.font_sm.render(
                    f"{loc.tagline}  ·  finds: {kinds}  ·  ${loc.travel_cost} / {loc.travel_hours:.0f}h",
                    True,
                    theme.TEXT_DIM,
                ),
                (rect.x + 14, rect.y + 34),
            )
            can = (
                not locked
                and self.state.money >= loc.travel_cost
                and self.state._count_free_pots() >= 1
            )
            b = Button(
                pygame.Rect(rect.right - 130, rect.y + 14, 110, 34),
                "Explore",
                f"explore:{loc.id}",
                enabled=can,
            )
            self.buttons.append(b)
            b.draw(self.screen, self.font_sm)
            y += 70

        b = Button(pygame.Rect(panel.x + 24, panel.bottom - 50, 120, 32), "Back", "goto:greenhouse")
        self.buttons.append(b)
        b.draw(self.screen, self.font_sm)

    def _draw_lab(self) -> None:
        panel = pygame.Rect(40, 90, WIDTH - 80, HEIGHT - 200)
        self._panel(panel)
        self.screen.blit(
            self.font_lg.render("Radiation Chamber", True, theme.ACCENT),
            (panel.x + 24, panel.y + 16),
        )
        unlocked = self.state.has_radiation_access()
        status = (
            "ONLINE — handle with tongs"
            if unlocked
            else "LOCKED — visit Abandoned Lab or buy chamber kit"
        )
        self.screen.blit(
            self.font_sm.render(status, True, theme.GOOD if unlocked else theme.DANGER),
            (panel.x + 24, panel.y + 52),
        )
        self.screen.blit(
            self.font_sm.render(
                "Force mutations into a specimen. Severe can destroy it. Irradiated crosses: Breed bench.",
                True,
                theme.TEXT_DIM,
            ),
            (panel.x + 24, panel.y + 78),
        )

        plant = self.state.plants.get(self.selected_id) if self.selected_id else None
        if plant and not plant.sold:
            self.screen.blit(
                self.font.render(f"Selected: {plant.name}", True, theme.TEXT),
                (panel.x + 24, panel.y + 110),
            )
            draw_plant(self.screen, plant, (panel.x + 200, panel.y + 280), 120, self.time_s)
        else:
            self.screen.blit(
                self.font.render("Select a specimen from the greenhouse first.", True, theme.DANGER),
                (panel.x + 24, panel.y + 110),
            )

        y = panel.y + 160
        for intensity, label, cost in [
            ("mild", "Mild dose", 15),
            ("standard", "Standard blast", 25),
            ("severe", "Severe cook", 40),
        ]:
            can = unlocked and plant is not None and not plant.sold and self.state.money >= cost
            b = Button(
                pygame.Rect(panel.x + 360, y, 280, 40),
                f"{label} (${cost})",
                f"irradiate:{intensity}",
                enabled=can,
            )
            self.buttons.append(b)
            b.draw(self.screen, self.font)
            y += 52

        if self.state.last_radiation:
            lr = self.state.last_radiation
            box = pygame.Rect(panel.x + 680, panel.y + 160, 360, 200)
            pygame.draw.rect(self.screen, theme.PANEL_INNER, box, border_radius=8)
            self.screen.blit(self.font.render("Last blast", True, theme.GOLD), (box.x + 12, box.y + 10))
            self.screen.blit(
                self.font_sm.render(
                    f"{lr.get('plant_name')} — {lr.get('intensity')}",
                    True,
                    theme.TEXT,
                ),
                (box.x + 12, box.y + 40),
            )
            gained = lr.get("mutations_gained") or []
            self.screen.blit(
                self.font_sm.render(
                    f"Gained alleles: {len(gained)}"
                    + (" (survived)" if lr.get("survived") else " DESTROYED"),
                    True,
                    theme.TEXT,
                ),
                (box.x + 12, box.y + 66),
            )
            yy = box.y + 94
            for note in (lr.get("notes") or [])[:4]:
                self.screen.blit(
                    self.font_sm.render(note[:42], True, theme.TEXT_DIM),
                    (box.x + 12, yy),
                )
                yy += 20

        b = Button(pygame.Rect(panel.x + 24, panel.bottom - 50, 120, 32), "Back", "goto:greenhouse")
        self.buttons.append(b)
        b.draw(self.screen, self.font_sm)

    def _draw_help(self) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 20, 14, 200))
        self.screen.blit(overlay, (0, 0))
        box = pygame.Rect(180, 100, WIDTH - 360, HEIGHT - 200)
        self._panel(box)
        lines = [
            "Sine Farm — Help",
            "",
            "Breeding is the game. Plants are drawn from sine stems and weird genes.",
            "",
            "Greenhouse / Wait — grow specimens",
            "Shop — seeds & upgrades (incl. Radiation Chamber Kit)",
            "Travel — simulated expeditions; wild plants, fungi, mossbeasts…",
            "Lab — radiation chamber: force mutations / risk destruction",
            "Breed — normal or irradiated crosses (cross-kingdom allowed)",
            "Trial Shows — cheap grades to decide keep vs sell (test-race vibe)",
            "Compete — real shows for money & prestige",
            "Catalog — discoveries; unknowns stay ???",
            "",
            "S — save    H — help    Esc — back/quit    Ctrl+N — new game",
        ]
        y = box.y + 24
        for i, line in enumerate(lines):
            font = self.font_lg if i == 0 else self.font_sm
            color = theme.ACCENT if i == 0 else theme.TEXT
            self.screen.blit(font.render(line, True, color), (box.x + 28, y))
            y += 28 if i == 0 else 22

    def _blip_plant(self, plant, kind: str = "mature") -> None:
        try:
            morph = morph_from_phenotype(
                plant.phenotype(),
                seed=seed_from_plant_id(plant.id),
                label=plant.name,
            )
            blip_from_morph(morph, kind=kind)
        except Exception:
            pass

    def _blip_named(self, name: str, kind: str = "mature") -> None:
        for p in self.state.living_plants():
            if p.name == name:
                self._blip_plant(p, kind)
                return

    def _blit_wrapped(
        self,
        text: str,
        font: pygame.font.Font,
        color,
        rect: pygame.Rect,
        max_width: int,
    ) -> None:
        words = text.split()
        lines: List[str] = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        y = rect.y
        for line in lines[:4]:
            self.screen.blit(font.render(line, True, color), (rect.x, y))
            y += font.get_height() + 2


def main() -> None:
    LovelyFlowersApp().run()


if __name__ == "__main__":
    main()

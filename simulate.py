#!/usr/bin/env python3
"""Headless greenhouse simulation — exercises genetics without Pygame."""

from __future__ import annotations

import argparse
import random

from game.names import humorous_description
from game.state import GameState
from genetics.mutations import MUTATION_CATALOG
from genetics.plant import breed, create_seed_plant


def demo_lineage(generations: int = 12, seed: int = 7) -> None:
    rng = random.Random(seed)
    a = create_seed_plant("Mavis", rng=rng, quality="premium")
    b = create_seed_plant("Kevin", rng=rng, quality="premium")
    print(f"Founders: {a.name} & {b.name}")
    print(f"  {a.name}: value ${a.value:.1f}, mut={a.expressed_mutation_names()}")
    print(f"  {b.name}: value ${b.value:.1f}, mut={b.expressed_mutation_names()}")

    line_parent = a
    other = b
    for gen in range(2, generations + 1):
        child = breed(line_parent, other, f"Lineage-{gen}", rng=rng)
        ph = child.phenotype()
        muts = [MUTATION_CATALOG[m].name for m in ph.expressed_mutations]
        carriers = [MUTATION_CATALOG[m].name for m in ph.carrier_mutations]
        print(
            f"Gen {child.generation}: {child.name}  "
            f"beauty={ph.beauty:.2f} size={ph.size_score:.2f} "
            f"strange={ph.strangeness:.2f} value=${ph.value:.1f}"
        )
        if muts:
            print(f"   EXPRESSED: {', '.join(muts)}")
        if carriers:
            print(f"   carriers: {', '.join(carriers)}")
        print(f"   {humorous_description(child)}")
        # Keep best-ish parent for next generation
        if child.value >= line_parent.value or ph.expressed_mutations:
            other = line_parent
            line_parent = child
        else:
            other = child


def demo_game(days: int = 40, seed: int = 99) -> None:
    gs = GameState.new_game(seed=seed)
    print(f"Starting money ${gs.money:.1f}, plant: {list(gs.plants.values())[0].name}")

    # Buy more seeds and grow until we have breeding stock
    gs.money = max(gs.money, 200)
    gs.buy_seed("premium")
    gs.buy_seed("common")
    for _ in range(60):
        gs.advance_time(12)

    mature = [p for p in gs.living_plants() if p.mature]
    print(f"Mature plants: {[p.name for p in mature]}")
    if len(mature) >= 2:
        kids = gs.breed_plants(mature[0].id, mature[1].id)
        print(f"Breeding produced: {[k.name for k in kids]}")
        for _ in range(60):
            gs.advance_time(12)
        kids_mature = [gs.plants[k.id] for k in kids if k.id in gs.plants and gs.plants[k.id].mature]
        if kids_mature:
            best = max(kids_mature, key=lambda p: p.value)
            print(f"Best offspring: {best.name} gen{best.generation} ${best.value:.1f}")
            print(f"  {humorous_description(best)}")
            result = gs.enter_competition("peoples_pot", best.id)
            if result:
                print(f"Contest: {result.ribbon} place {result.place} — ${result.prize}")

    print(f"Day {gs.day:.1f} | ${gs.money:.1f} | prestige {gs.prestige}")
    print(f"Mutations discovered: {sorted(gs.collection.mutations) or 'none yet'}")
    print(f"Max generation: {gs.collection.max_generation}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Headless Sine Farm simulation")
    parser.add_argument("--lineage", type=int, default=0, help="Breed N generations")
    parser.add_argument("--game", action="store_true", help="Simulate game loop")
    parser.add_argument("--morph-demo", action="store_true", help="Write morph preview PNG")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--out",
        type=str,
        default="data/previews/sine_farm_morph.png",
        help="Output path for --morph-demo",
    )
    args = parser.parse_args()
    if args.morph_demo:
        import os
        from pathlib import Path

        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        from procgen.preview import save_gallery

        path = save_gallery(Path(args.out))
        print(f"Wrote morph demo {path}")
        return
    if args.lineage:
        demo_lineage(args.lineage, seed=args.seed)
    if args.game or not args.lineage:
        demo_game(seed=args.seed)


if __name__ == "__main__":
    main()

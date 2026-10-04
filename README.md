# Lovely Flowers

A small single-player plant breeding and collection game.

**Collect → breed → genetically improve → compete → sell → repeat.**

Inspired by the simple outer loop of [Horsey Game](https://store.steampowered.com/app/3602570/Horsey_Game/) (Captain Games), translated into plants — with a genetics engine taken far too seriously.

## Play

```bash
pip install -r requirements.txt
python main.py
```

| Key / Control | Action |
|---|---|
| Click pot | Inspect plant |
| Space / Wait | Advance time (+8 hours) |
| Shop | Buy seeds & upgrades |
| Breed | Cross-pollinate two mature plants |
| Compete | Enter plant shows |
| Collection | Mutations, bloodlines, ribbons |
| S | Save |
| H | Help |
| Esc | Back / quit |
| Ctrl+N | New game |

Saves to `data/save.json`.

## Design

- **Breeding is progression** — not a tech tree.
- **Simple economy** — sell unwanted plants, win prize money. No customers or supply chains.
- **Competitions** replace racing: Grand Flower Show, Giant's Cup, Speed Grow, Botanical Abomination, People's Pot.
- **Genuine genetics** — diploid alleles, dominance, recessives, carriers, trade-offs, heritable mutations.
- **Pedigree & attachment** — named specimens, bloodlines, generation tracking.

The comedy is the contrast between a serious breeding sim and a plant with six eyes.

## Headless simulation / tests

The genetics engine has **no Pygame dependency** and can be exercised alone:

```bash
python simulate.py --lineage 15 --seed 7
python simulate.py --game
pytest -q
```

## Project layout

```
genetics/          # Pure genetics simulator (testable without UI)
game/              # Greenhouse state, competitions, collection, names
ui/                # Pygame front-end + procedural plant renderer
tests/             # Unit tests for inheritance, mutations, game loop
main.py            # Launch the game
simulate.py        # Headless demo
```

## Mutations (examples)

Giant leaves, spiral growth, dense bloom, bioluminescence, feather leaves, eye-like structures, leg-like roots, face-like flowers, multi-stem, chromatic drift, translucent stem, sonic bloom.

Unknown discoveries appear as `???` until expressed and logged.
